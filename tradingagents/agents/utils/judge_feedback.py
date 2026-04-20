from typing import Any, Dict, List


def build_judge_feedback_block(
    state: Dict[str, Any],
    feedback_key: str,
    node_name: str,
) -> str:
    feedback_map = state.get("judge_feedback", {}) or {}
    score_map = state.get("judge_scores", {}) or {}

    feedback = str(feedback_map.get(feedback_key, "") or "").strip()
    score_info = score_map.get(node_name, {}) or {}
    missing_items = score_info.get("missing_items", []) or []
    score = score_info.get("score")

    normalized_missing_items: List[str] = [
        str(item).strip() for item in missing_items if str(item).strip()
    ]

    if not feedback and not normalized_missing_items:
        return ""

    lines = [
        "",
        "## 上一轮质量评审反馈",
        "你当前正在对上一版输出进行定向修订，而不是从零开始随意重写。",
        "请优先保留上一版中已有价值的分析，只补齐缺失项、修正空泛表达，并强化证据、结论和可执行性。",
    ]
    if score is not None:
        lines.append(f"- 上一轮评分：{score}/10")
    if feedback:
        lines.append(f"- 修改意见：{feedback}")
    if normalized_missing_items:
        lines.append(f"- 必须补齐项：{', '.join(normalized_missing_items)}")
    lines.append("- 如果上一版已经有正确内容，请在保留其有效部分的基础上增量修正。")
    lines.append("- 不要忽略以上反馈，否则本轮结果仍会被判定为低质量。")
    lines.append("")

    return "\n".join(lines)
