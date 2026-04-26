from __future__ import annotations

from typing import Any, Dict, Iterable, List

from tradingagents.quality_gates import evaluate_quality_gates


def filter_allowed_tools(tools: Iterable[Any], allowed_tools: List[str]) -> List[Any]:
    """Filter runtime tools by skill allowlist.

    If allowlist is empty, keep original tool set to preserve backward compatibility.
    """
    allowed = {name for name in (allowed_tools or []) if name}
    if not allowed:
        return list(tools)

    filtered: List[Any] = []
    for tool in tools:
        current_tool_name = getattr(tool, "name", None) or getattr(tool, "__name__", None)
        if current_tool_name in allowed:
            filtered.append(tool)
    return filtered


def run_quality_gates(result: Dict[str, Any], quality_gates: List[str]) -> Dict[str, Any]:
    return evaluate_quality_gates(result, quality_gates)
