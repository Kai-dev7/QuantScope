from __future__ import annotations

from typing import Any, Dict

from .models import QualityGateResult


def evaluate(result: Dict[str, Any]) -> QualityGateResult:
    summary = str(result.get("summary", "") or "").strip()
    recommendation = str(result.get("recommendation", "") or "").strip()
    reports = result.get("reports") or {}
    detailed_analysis = result.get("detailed_analysis") or {}

    checks = {
        "summary": len(summary) >= 20,
        "recommendation": len(recommendation) >= 10,
        "reports": bool(reports),
        "detailed_analysis": bool(detailed_analysis),
    }
    score = sum(1 for ok in checks.values() if ok)
    return QualityGateResult(
        gate="report_completeness_check",
        passed=score >= 3,
        score=score,
        severity="blocking",
        message=f"Completeness score={score}/4",
        details=checks,
    )
