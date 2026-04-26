from __future__ import annotations

from typing import Dict

from .models import CapabilityResult


class SandboxHands:
    def execute(self, capability_name: str, arguments: Dict[str, object], session_context: Dict[str, object]) -> CapabilityResult:
        return CapabilityResult(
            success=False,
            capability_name=capability_name,
            error="Sandbox hands not implemented in phase 1",
            metadata={"session_context": session_context},
        )
