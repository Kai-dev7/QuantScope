"""
股票实体提取服务

优先使用当前系统配置的大模型从自然语言目标中提取股票名称/代码，
失败时返回空结果，由前端/调用方继续走规则兜底。
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import httpx

from app.core.database import get_mongo_db
from app.core.unified_config import UnifiedConfigManager
from app.services.simple_analysis_service import get_provider_and_url_by_model_sync

logger = logging.getLogger("webapi")


class StockExtractionService:
    def __init__(self) -> None:
        self.unified_config = UnifiedConfigManager()
        self._stock_cache: Dict[str, Any] = {}
        self._stock_cache_time: Dict[str, datetime] = {}

    async def extract_from_prompt(self, prompt: str, model_name: Optional[str] = None) -> Dict[str, Any]:
        text = (prompt or "").strip()
        if not text:
            return self._empty_result("empty_prompt")

        # 1. 优先从 MongoDB 基础信息库搜索，避免每次实时调用外部数据源。
        db_match = await self._match_stock_from_db(text)
        if db_match:
            return db_match

        # 2. AKShare A股搜索兜底。
        try:
            import akshare as ak

            a_share_df = ak.stock_info_a_code_name()
            # 匹配：股票名称 in 用户输入（如 "江西铜业" in "给我分析江西铜业"）
            mask = a_share_df["name"].apply(lambda n: n in text)
            if not mask.any():
                mask = a_share_df["code"].apply(lambda c: c in text)
            matches = a_share_df[mask].head(3)
            if not matches.empty:
                first = matches.iloc[0]
                logger.info("✅ [akshare A股命中] '%s' -> %s (%s)", text, first["name"], first["code"])
                return {
                    "stock_name": str(first["name"]),
                    "stock_code": str(first["code"]),
                    "market": "CN",
                    "confidence": 0.95,
                    "reason": "akshare A股兜底匹配",
                    "matched": True,
                }
        except Exception as exc:
            logger.debug("akshare A股搜索失败（不影响后续）: %s", exc)

        # 3. LLM 提取
        model_name = (model_name or "").strip() or self.unified_config.get_default_model()
        provider_info = get_provider_and_url_by_model_sync(model_name)
        backend_url = provider_info.get("backend_url")
        api_key = provider_info.get("api_key")

        if not backend_url or not api_key:
            logger.warning("股票提取跳过模型调用: backend_url/api_key 缺失")
            return self._empty_result("llm_not_configured")

        try:
            raw = await self._call_openai_compatible_llm(
                backend_url=backend_url,
                api_key=api_key,
                model_name=model_name,
                prompt=text,
            )
            parsed = self._parse_llm_result(raw)
            parsed["provider"] = provider_info.get("provider")
            parsed["model"] = model_name
            return parsed
        except Exception as exc:
            logger.warning("模型提取股票失败，回退规则: %s", exc)
            return self._empty_result("llm_failed")

    async def _match_stock_from_db(self, text: str) -> Optional[Dict[str, Any]]:
        """从 MongoDB 的基础信息集合匹配股票名称/代码。"""
        try:
            stocks = await self._get_stock_cache()
            if not stocks:
                return None

            for stock in stocks:
                name = str(stock.get("name") or "").strip()
                name_en = str(stock.get("name_en") or "").strip()
                code = str(stock.get("code") or "").strip()
                market = str(stock.get("market_type") or stock.get("_market") or "").strip()
                if not code or not market:
                    continue
                if (name and name in text) or (name_en and name_en.lower() in text.lower()) or code in text:
                    stock_name = name or name_en or code
                    logger.info("✅ [MongoDB股票命中] '%s' -> %s (%s, %s)", text, stock_name, code, market)
                    return {
                        "stock_name": stock_name,
                        "stock_code": code,
                        "market": market,
                        "confidence": 0.95,
                        "reason": "MongoDB 股票基础信息匹配",
                        "matched": True,
                    }
        except Exception as exc:
            logger.debug("MongoDB股票搜索失败（不影响后续）: %s", exc)

        return None

    async def _get_stock_cache(self):
        """读取并短时缓存股票基础信息，减少重复数据库扫描。"""
        now = datetime.utcnow()
        cache_key = "all"
        if (
            cache_key in self._stock_cache
            and cache_key in self._stock_cache_time
            and now - self._stock_cache_time[cache_key] < timedelta(hours=1)
        ):
            return self._stock_cache[cache_key]

        db = get_mongo_db()
        collection_map = {
            "CN": "stock_basic_info",
            "HK": "stock_basic_info_hk",
            "US": "stock_basic_info_us",
        }

        docs = []
        for market, collection_name in collection_map.items():
            cursor = db[collection_name].find(
                {
                    "code": {"$exists": True, "$ne": ""},
                    "$or": [
                        {"name": {"$exists": True, "$ne": ""}},
                        {"name_en": {"$exists": True, "$ne": ""}},
                    ],
                },
                {"_id": 0, "code": 1, "name": 1, "name_en": 1, "source": 1, "market_type": 1},
            )
            market_docs = await cursor.to_list(length=None)
            for doc in market_docs:
                doc["_market"] = market
            docs.extend(market_docs)

        source_priority = {"tushare": 0, "akshare": 1, "baostock": 2}
        unique = {}
        for doc in docs:
            code = str(doc.get("code") or "").strip()
            market = str(doc.get("_market") or "").strip()
            if not code:
                continue
            unique_key = f"{market}:{code}"
            current = unique.get(unique_key)
            if not current:
                unique[unique_key] = doc
                continue
            current_rank = source_priority.get(str(current.get("source") or ""), 99)
            doc_rank = source_priority.get(str(doc.get("source") or ""), 99)
            if doc_rank < current_rank:
                unique[unique_key] = doc

        self._stock_cache[cache_key] = sorted(
            unique.values(),
            key=lambda item: max(len(str(item.get("name") or "")), len(str(item.get("name_en") or ""))),
            reverse=True,
        )
        self._stock_cache_time[cache_key] = now
        logger.info("📚 股票基础信息缓存加载完成: %s 条", len(self._stock_cache[cache_key]))
        return self._stock_cache[cache_key]

    async def _call_openai_compatible_llm(
        self,
        backend_url: str,
        api_key: str,
        model_name: str,
        prompt: str,
    ) -> str:
        normalized = backend_url.rstrip("/")
        if not re.search(r"/v\d+$", normalized):
            normalized = f"{normalized}/v1"

        url = f"{normalized}/chat/completions"
        system_prompt = (
            "你是股票实体提取器。"
            "从用户输入中提取唯一最相关的股票信息。"
            "只返回 JSON，不要返回解释。"
            'JSON 格式: {"stock_name":"", "stock_code":"", "market":"CN|HK|US|", "confidence":0到1, "reason":""}。'
            "如果无法确定，请保持字段为空字符串，confidence 设为 0。"
            "market 仅允许 CN/HK/US。"
        )

        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0,
            "max_tokens": 200,
            "response_format": {"type": "json_object"},
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
                .strip()
            )

    def _parse_llm_result(self, content: str) -> Dict[str, Any]:
        if not content:
            return self._empty_result("empty_content")

        try:
            payload = json.loads(content)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", content, re.S)
            if not match:
                return self._empty_result("invalid_json")
            payload = json.loads(match.group(0))

        market = str(payload.get("market", "")).strip().upper()
        if market not in {"CN", "HK", "US"}:
            market = ""

        stock_name = str(payload.get("stock_name", "")).strip()
        stock_code = str(payload.get("stock_code", "")).strip().upper()

        confidence_raw = payload.get("confidence", 0)
        try:
            confidence = float(confidence_raw)
        except (TypeError, ValueError):
            confidence = 0.0

        return {
            "stock_name": stock_name,
            "stock_code": stock_code,
            "market": market,
            "confidence": max(0.0, min(confidence, 1.0)),
            "reason": str(payload.get("reason", "")).strip(),
            "matched": bool(stock_name or stock_code),
        }

    @staticmethod
    def _empty_result(reason: str) -> Dict[str, Any]:
        return {
            "stock_name": "",
            "stock_code": "",
            "market": "",
            "confidence": 0.0,
            "reason": reason,
            "matched": False,
        }


stock_extraction_service = StockExtractionService()
