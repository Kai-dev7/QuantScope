"""
轻量级 Planner Agent 服务。

当前实现采用规则规划，负责在正式分析前产出结构化计划：
- 动态选择分析师
- 推断分析深度
- 生成 focus_hint 注入下游分析上下文

后续如需升级为 LLM Planner，可直接替换本模块实现，保持返回结构不变。
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional
import logging
import re

logger = logging.getLogger(__name__)

VALID_ANALYSTS = ["market", "fundamentals", "news", "social"]


@dataclass
class PlannerResult:
    analysts: List[str]
    depth: str
    focus_hint: str
    reasoning: List[str]
    user_goal: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PlannerService:
    """根据股票代码和分析目标生成结构化分析计划。"""

    def plan(
        self,
        symbol: str,
        user_goal: Optional[str] = None,
        selected_analysts: Optional[List[str]] = None,
        research_depth: Optional[str] = None,
    ) -> PlannerResult:
        goal = (user_goal or "").strip()
        analysts = self._plan_analysts(goal, selected_analysts)
        depth = self._plan_depth(goal, research_depth)
        focus_hint, reasoning = self._plan_focus(symbol, goal, analysts)

        result = PlannerResult(
            analysts=analysts,
            depth=depth,
            focus_hint=focus_hint,
            reasoning=reasoning,
            user_goal=goal,
        )
        logger.info("Planner 生成计划: %s", result.to_dict())
        return result

    def _plan_analysts(
        self,
        goal: str,
        selected_analysts: Optional[List[str]],
    ) -> List[str]:
        normalized_selected = [
            analyst for analyst in (selected_analysts or []) if analyst in VALID_ANALYSTS
        ]
        goal_lower = goal.lower()
        analysts = set(normalized_selected or ["market", "fundamentals"])
        reasons: List[str] = []

        keyword_map = {
            "fundamentals": [
                "财报", "业绩", "估值", "盈利", "利润", "营收", "毛利", "现金流",
                "资产负债", "roe", "pe", "pb", "基本面", "分红", "库存",
            ],
            "news": [
                "新闻", "公告", "政策", "事件", "舆情", "催化", "财报影响", "业绩预告",
                "监管", "并购", "合作", "订单", "研报",
            ],
            "social": [
                "社交", "情绪", "社区", "股吧", "微博", "热度", "讨论", "舆论", "散户情绪",
            ],
            "market": [
                "技术", "走势", "价格", "量价", "资金", "趋势", "交易", "动量", "波动",
                "市场", "短线", "筹码",
            ],
        }

        for analyst, keywords in keyword_map.items():
            if any(keyword in goal_lower for keyword in keywords):
                analysts.add(analyst)
                reasons.append(analyst)

        # 如果目标明显是事件/财报影响，默认跳过 social，除非用户明确要求。
        if any(term in goal_lower for term in ["财报", "公告", "业绩", "政策", "新闻", "事件"]) and not any(
            term in goal_lower for term in keyword_map["social"]
        ):
            analysts.discard("social")

        ordered = [analyst for analyst in VALID_ANALYSTS if analyst in analysts]
        return ordered or ["market", "fundamentals"]

    def _plan_depth(self, goal: str, research_depth: Optional[str]) -> str:
        if research_depth:
            return research_depth

        if not goal:
            return "标准"

        deep_keywords = [
            "深度", "详细", "全面", "拆解", "重点", "影响", "风险", "财报", "估值", "预期",
            "比较", "变化", "拐点", "库存", "现金流", "业绩",
        ]
        hit_count = sum(1 for keyword in deep_keywords if keyword in goal.lower())
        if hit_count >= 3:
            return "深度"
        if hit_count >= 1:
            return "标准"
        return "基础"

    def _plan_focus(
        self,
        symbol: str,
        goal: str,
        analysts: List[str],
    ) -> tuple[str, List[str]]:
        reasoning: List[str] = []
        focus_parts: List[str] = []

        if goal:
            cleaned_goal = re.sub(r"\s+", " ", goal).strip("，。；; ")
            focus_parts.append(f"用户关注点：{cleaned_goal}")
            reasoning.append("根据用户分析目标提取重点")

        if "fundamentals" in analysts:
            if any(term in goal for term in ["财报", "业绩"]):
                focus_parts.append("重点检查最近一期营收、利润、毛利率、现金流和存货/应收变化")
                reasoning.append("目标涉及财报/业绩，强化基本面细项")
            elif any(term in goal.lower() for term in ["估值", "pe", "pb", "roe"]):
                focus_parts.append("重点检查估值指标、盈利质量和同行对比")
                reasoning.append("目标涉及估值，强化估值与盈利质量")

        if "news" in analysts:
            focus_parts.append("重点筛查近7天高相关公告、政策与事件催化")
            reasoning.append("纳入新闻分析，要求关注近期事件")

        if "market" in analysts:
            focus_parts.append("重点结合近期价格趋势、成交量和市场反应验证基本面/事件影响")
            reasoning.append("纳入市场分析，要求交叉验证价格反应")

        if "social" in analysts:
            focus_parts.append("重点观察社交情绪是否与基本面和新闻出现背离")
            reasoning.append("纳入社交分析，检查情绪背离")

        if not focus_parts:
            focus_parts.append(f"围绕 {symbol} 的核心驱动因素做标准化多维分析")
            reasoning.append("未识别到明确目标，回退到标准化分析")

        return "；".join(focus_parts), reasoning


planner_service = PlannerService()
