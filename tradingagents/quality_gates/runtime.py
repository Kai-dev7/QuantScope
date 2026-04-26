from __future__ import annotations

from typing import Any, Dict, List

from .models import QualityGateResult, QualityGateRunResult
from .registry import get_default_quality_gate_registry


def evaluate_quality_gates(result: Dict[str, Any], quality_gates: List[str]) -> Dict[str, Any]:
    registry = get_default_quality_gate_registry()
    outputs: List[QualityGateResult] = []

    for gate_name in quality_gates or []:
        definition = registry.get(gate_name)
        if definition is None:
            outputs.append(
                QualityGateResult(
                    gate=gate_name,
                    passed=True,
                    score=None,
                    severity="info",
                    message="Skipped: unknown gate",
                )
            )
            continue

        gate_result = definition.evaluator(result)
        gate_result.severity = gate_result.severity or definition.default_severity
        outputs.append(gate_result)

    blocking_failed = any((not item.passed) and item.severity == "blocking" for item in outputs)
    warning_count = sum(1 for item in outputs if (not item.passed) and item.severity != "blocking")
    failed_gates = [item.gate for item in outputs if not item.passed]

    if blocking_failed:
        status = "failed"
        degrade_to = "needs_regeneration"
    elif warning_count:
        status = "warning"
        degrade_to = "completed_with_warnings"
    else:
        status = "passed"
        degrade_to = None

    return QualityGateRunResult(
        passed=not blocking_failed,
        status=status,
        blocking_failed=blocking_failed,
        warning_count=warning_count,
        degrade_to=degrade_to,
        failed_gates=failed_gates,
        results=[item.to_dict() for item in outputs],
    ).to_dict()
