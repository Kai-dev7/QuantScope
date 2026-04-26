from __future__ import annotations

from typing import Any, Callable, Dict, Optional


class CapabilityRegistry:
    def __init__(self) -> None:
        self._capabilities: Dict[str, Any] = {}

    def register(self, name: str, capability: Any) -> None:
        self._capabilities[name] = capability

    def get(self, name: str) -> Optional[Any]:
        return self._capabilities.get(name)

    def has(self, name: str) -> bool:
        return name in self._capabilities


capability_registry = CapabilityRegistry()
