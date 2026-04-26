from __future__ import annotations

from typing import Any, Dict

from .models import QualityGateResult


def evaluate(result: Dict[str, Any]) -> QualityGateResult:
    decision = result.get("decision") or {}
    target_price = decision.get("target_price")
    passed = target_price is None or isinstance(target_price, (int, float))
    return QualityGateResult(
        gate="target_price_sanity_check",
        passed=passed,
        score=1 if passed else 0,
        severity="warning",
        message="Target price format looks sane" if passed else "Target price format is invalid",
    )
