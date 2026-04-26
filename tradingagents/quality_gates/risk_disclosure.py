from __future__ import annotations

from typing import Any, Dict

from .models import QualityGateResult


def evaluate(result: Dict[str, Any]) -> QualityGateResult:
    risk_level = str(result.get("risk_level", "") or "")
    recommendation = str(result.get("recommendation", "") or "").lower()
    summary = str(result.get("summary", "") or "").lower()
    has_risk_signal = (
        bool(risk_level.strip())
        or ("风险" in recommendation)
        or ("risk" in recommendation)
        or ("风险" in summary)
    )
    return QualityGateResult(
        gate="risk_disclosure_check",
        passed=has_risk_signal,
        score=1 if has_risk_signal else 0,
        severity="warning",
        message="Risk disclosure detected" if has_risk_signal else "Risk disclosure missing",
    )
