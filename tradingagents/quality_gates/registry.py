from __future__ import annotations

from typing import Dict, Optional

from . import report_completeness, risk_disclosure, target_price_sanity
from .models import QualityGateDefinition


class QualityGateRegistry:
    def __init__(self) -> None:
        self._definitions: Dict[str, QualityGateDefinition] = {}

    def register(self, definition: QualityGateDefinition) -> None:
        self._definitions[definition.name] = definition

    def get(self, name: str) -> Optional[QualityGateDefinition]:
        return self._definitions.get(name)


_default_registry: QualityGateRegistry | None = None


def get_default_quality_gate_registry() -> QualityGateRegistry:
    global _default_registry
    if _default_registry is None:
        registry = QualityGateRegistry()
        registry.register(
            QualityGateDefinition(
                name="report_completeness_check",
                evaluator=report_completeness.evaluate,
                blocking=True,
                default_severity="blocking",
            )
        )
        registry.register(
            QualityGateDefinition(
                name="risk_disclosure_check",
                evaluator=risk_disclosure.evaluate,
                blocking=False,
                default_severity="warning",
            )
        )
        registry.register(
            QualityGateDefinition(
                name="target_price_sanity_check",
                evaluator=target_price_sanity.evaluate,
                blocking=False,
                default_severity="warning",
            )
        )
        _default_registry = registry
    return _default_registry
