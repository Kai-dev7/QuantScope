from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


ALLOWED_ANALYSTS = {"market", "fundamentals", "news", "social"}


@dataclass
class SkillSelectorRule:
    task_type: str
    market_scopes: List[str] = field(default_factory=list)
    research_depths: List[str] = field(default_factory=list)


@dataclass
class SkillInputs:
    required: List[str] = field(default_factory=list)
    optional: List[str] = field(default_factory=list)


@dataclass
class SkillAnalysts:
    enabled: List[str] = field(default_factory=list)
    optional: List[str] = field(default_factory=list)


@dataclass
class SkillToolPolicy:
    allowed_tools: List[str] = field(default_factory=list)
    max_tool_calls: Dict[str, int] = field(default_factory=dict)


@dataclass
class SkillExecutionPolicy:
    debate_rounds: int = 1
    risk_rounds: int = 1
    memory_enabled: bool = True
    llm_routing: str = "default"


@dataclass
class SkillOutputContract:
    schema: str = "stock_analysis_v1"
    required_sections: List[str] = field(default_factory=list)


@dataclass
class SkillDefinition:
    name: str
    version: int
    description: str
    selectors: SkillSelectorRule
    inputs: SkillInputs
    analysts: SkillAnalysts
    tool_policy: SkillToolPolicy
    execution: SkillExecutionPolicy
    output: SkillOutputContract
    quality_gates: List[str] = field(default_factory=list)
    fallback: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SkillMatchContext:
    task_type: str
    market_scope: str
    research_depth: str
    extra: Dict[str, Any] = field(default_factory=dict)


def normalize_skill_name(name: str) -> str:
    return str(name or "").strip().lower()
