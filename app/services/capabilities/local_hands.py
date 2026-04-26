from __future__ import annotations

from typing import Any, Dict

from .models import CapabilityResult


class LocalHands:
    def execute(self, capability: Any, arguments: Dict[str, Any]) -> CapabilityResult:
        try:
            result = capability.invoke(arguments)
            return CapabilityResult(
                success=True,
                capability_name=getattr(capability, "name", None) or getattr(capability, "__name__", "unknown"),
                result=result,
            )
        except Exception as exc:
            return CapabilityResult(
                success=False,
                capability_name=getattr(capability, "name", None) or getattr(capability, "__name__", "unknown"),
                error=str(exc),
            )
