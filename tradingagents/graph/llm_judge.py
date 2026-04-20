import json
from typing import Any, Dict, Optional

from tradingagents.utils.logging_init import get_logger

logger = get_logger("agents")


# 仅保留 3 个高杠杆节点的 Judge：
# - Research Manager: 汇总多源分析并形成投资计划
# - Trader: 生成可执行交易方案
# - Risk Judge: 输出最终风险裁决
# 这样可以避免在前置分析节点上重复评审，降低整体时延。
JUDGE_TARGETS: Dict[str, Dict[str, Any]] = {
    "Research Manager": {
        "output_key": "investment_plan",
        "feedback_key": "research_manager",
        "required_items": ["明确建议", "理由", "目标价格"],
    },
    "Trader": {
        "output_key": "trader_investment_plan",
        "feedback_key": "trader",
        "required_items": ["买入/持有/卖出", "目标价位", "风险评分", "置信度"],
    },
    "Risk Judge": {
        "output_key": "final_trade_decision",
        "feedback_key": "risk_manager",
        "required_items": ["明确建议", "风险", "执行建议"],
    },
}


def _get_nested_value(data: Dict[str, Any], key_path: str) -> str:
    current: Any = data
    for part in key_path.split("."):
        if not isinstance(current, dict):
            return ""
        current = current.get(part, "")
    if current is None:
        return ""
    return str(current)


class LLMJudge:
    def __init__(self, llm, min_score: int = 7):
        self.llm = llm
        self.min_score = min_score

    def should_judge(self, node_name: str) -> bool:
        return node_name in JUDGE_TARGETS

    def evaluate(self, node_name: str, state: Dict[str, Any], update: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        target = JUDGE_TARGETS.get(node_name)
        if not target:
            return None

        output_text = _get_nested_value(update, target["output_key"])
        if not output_text.strip():
            return {
                "passed": False,
                "score": 0,
                "feedback": "输出为空或未生成目标字段，请直接补全完整内容。",
                "missing_items": target["required_items"],
            }

        focus_hint = state.get("focus_hint", "")
        planner_plan = state.get("planner_plan", {})
        prompt = f"""
你是股票分析流水线的质量评审员。请严格评估以下节点输出是否达到进入下一阶段的质量门槛。

节点名称：{node_name}
股票代码：{state.get("company_of_interest", "")}
分析日期：{state.get("trade_date", "")}
Planner重点：{focus_hint}
Planner计划：{json.dumps(planner_plan, ensure_ascii=False)}
必须覆盖项：{", ".join(target["required_items"])}

请重点检查：
1. 是否回应了任务目标
2. 是否覆盖必须项
3. 是否有清晰证据和具体结论
4. 是否存在空话、模板话、明显遗漏
5. 是否可直接进入下一节点

待评估输出：
{output_text[:12000]}

只返回 JSON，不要加解释：
{{
  "score": 0-10的整数,
  "passed": true或false,
  "missing_items": ["缺失项1"],
  "feedback": "给作者的简短可执行修改意见，不超过120字"
}}
"""
        try:
            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, "content") else str(response)
            start = content.find("{")
            end = content.rfind("}")
            if start == -1 or end == -1:
                raise ValueError(f"judge输出不是JSON: {content[:200]}")
            parsed = json.loads(content[start:end + 1])
            parsed["score"] = int(parsed.get("score", 0))
            parsed["passed"] = bool(parsed.get("passed", False)) and parsed["score"] >= self.min_score
            parsed["missing_items"] = parsed.get("missing_items", []) or []
            parsed["feedback"] = parsed.get("feedback", "") or "请补齐缺失信息并增强证据和结论。"
            return parsed
        except Exception as e:
            logger.warning(f"⚠️ [LLM Judge] 评估失败，默认放行 {node_name}: {e}")
            return {
                "passed": True,
                "score": self.min_score,
                "missing_items": [],
                "feedback": "",
            }
