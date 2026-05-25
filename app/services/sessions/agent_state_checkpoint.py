from __future__ import annotations

from typing import Any, Dict, Optional

from langchain_core.messages import messages_from_dict, messages_to_dict


CHECKPOINT_STATE_KEYS = {
    "messages",
    "company_of_interest",
    "trade_date",
    "planner_plan",
    "focus_hint",
    "skill_name",
    "skill_tool_policy",
    "judge_feedback",
    "judge_scores",
    "session_id",
    "investment_debate_state",
    "risk_debate_state",
    "market_report",
    "fundamentals_report",
    "sentiment_report",
    "news_report",
    "investment_plan",
    "trader_investment_plan",
    "final_trade_decision",
    "parallel_runtime_messages",
}

NODE_ORDER = [
    "Market Analyst",
    "Social Analyst",
    "News Analyst",
    "Fundamentals Analyst",
    "Bull Researcher",
    "Bear Researcher",
    "Research Manager",
    "Trader",
    "Risky Analyst",
    "Safe Analyst",
    "Neutral Analyst",
    "Risk Judge",
]


def serialize_checkpoint_state(state: Dict[str, Any]) -> Dict[str, Any]:
    checkpoint_state = {
        key: state.get(key)
        for key in CHECKPOINT_STATE_KEYS
        if key in state
    }
    if "messages" in checkpoint_state:
        checkpoint_state["messages"] = messages_to_dict(checkpoint_state.get("messages") or [])
    return checkpoint_state


def deserialize_checkpoint_state(state: Dict[str, Any]) -> Dict[str, Any]:
    restored = dict(state or {})
    messages = restored.get("messages")
    if messages and isinstance(messages, list):
        try:
            restored["messages"] = messages_from_dict(messages)
        except Exception:
            restored["messages"] = []
    return restored


def next_node_after(node_name: str) -> Optional[str]:
    if not node_name:
        return None
    try:
        idx = NODE_ORDER.index(node_name)
    except ValueError:
        return None
    if idx + 1 >= len(NODE_ORDER):
        return "__end__"
    return NODE_ORDER[idx + 1]
