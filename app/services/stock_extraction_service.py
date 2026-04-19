"""
股票实体提取服务

优先使用当前系统配置的大模型从自然语言目标中提取股票名称/代码，
失败时返回空结果，由前端/调用方继续走规则兜底。
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, Optional

import httpx

from app.core.unified_config import UnifiedConfigManager
from app.services.simple_analysis_service import get_provider_and_url_by_model_sync

logger = logging.getLogger("webapi")


class StockExtractionService:
    def __init__(self) -> None:
        self.unified_config = UnifiedConfigManager()

    async def extract_from_prompt(self, prompt: str) -> Dict[str, Any]:
        text = (prompt or "").strip()
        if not text:
            return self._empty_result("empty_prompt")

        model_name = self.unified_config.get_default_model()
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
