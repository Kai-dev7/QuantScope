from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml

from .models import (
    SkillAnalysts,
    SkillDefinition,
    SkillExecutionPolicy,
    SkillInputs,
    SkillOutputContract,
    SkillSelectorRule,
    SkillToolPolicy,
)


def load_skill_from_yaml(path: str | Path) -> SkillDefinition:
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    return _build_skill(raw)


def _build_skill(raw: Dict[str, Any]) -> SkillDefinition:
    selectors = raw.get("selectors", {}) or {}
    inputs = raw.get("inputs", {}) or {}
    analysts = raw.get("analysts", {}) or {}
    tool_policy = raw.get("tool_policy", {}) or {}
    execution = raw.get("execution", {}) or {}
    output = raw.get("output", {}) or {}

    return SkillDefinition(
        name=str(raw.get("name", "")),
        version=int(raw.get("version", 1)),
        description=str(raw.get("description", "")),
        selectors=SkillSelectorRule(
            task_type=str(selectors.get("task_type", "")),
            market_scopes=list(selectors.get("market_scope", []) or selectors.get("market_scopes", []) or []),
            research_depths=list(selectors.get("research_depth", []) or selectors.get("research_depths", []) or []),
        ),
        inputs=SkillInputs(
            required=list(inputs.get("required", []) or []),
            optional=list(inputs.get("optional", []) or []),
        ),
        analysts=SkillAnalysts(
            enabled=list(analysts.get("enabled", []) or []),
            optional=list(analysts.get("optional", []) or []),
        ),
        tool_policy=SkillToolPolicy(
            allowed_tools=list(tool_policy.get("allowed_tools", []) or []),
            max_tool_calls=dict(tool_policy.get("max_tool_calls", {}) or {}),
        ),
        execution=SkillExecutionPolicy(
            debate_rounds=int(execution.get("debate_rounds", 1)),
            risk_rounds=int(execution.get("risk_rounds", 1)),
            memory_enabled=bool(execution.get("memory_enabled", True)),
            llm_routing=str(execution.get("llm_routing", "default")),
        ),
        output=SkillOutputContract(
            schema=str(output.get("schema", "stock_analysis_v1")),
            required_sections=list(output.get("required_sections", []) or []),
        ),
        quality_gates=list(raw.get("quality_gates", []) or []),
        fallback=dict(raw.get("fallback", {}) or {}),
        metadata=dict(raw.get("metadata", {}) or {}),
    )
