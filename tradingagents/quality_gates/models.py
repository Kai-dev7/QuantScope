from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Dict, List


@dataclass
class QualityGateResult:
    gate: str
    passed: bool
    score: int | None = None
    severity: str = "warning"
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class QualityGateDefinition:
    name: str
    evaluator: Callable[[Dict[str, Any]], QualityGateResult]
    blocking: bool = False
    default_severity: str = "warning"


@dataclass
class QualityGateRunResult:
    passed: bool
    status: str
    blocking_failed: bool
    warning_count: int
    degrade_to: str | None = None
    failed_gates: List[str] = field(default_factory=list)
    results: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
