from __future__ import annotations

import time
from typing import Any, Dict, Iterable, List

from app.services.sessions.event_store import session_event_store

from .local_hands import LocalHands
from .mcp_hands import MCPHands
from .models import CapabilityResult


class CapabilityExecutor:
    def __init__(self) -> None:
        self.local_hands = LocalHands()
        self.mcp_hands = MCPHands()

    def execute_local(
        self,
        capability: Any,
        arguments: Dict[str, Any],
        *,
        session_id: str = "",
        source: str = "local_tool",
    ) -> CapabilityResult:
        capability_name = getattr(capability, "name", None) or getattr(capability, "__name__", "unknown")
        start = time.time()

        if session_id:
            session_event_store.append_event_sync(
                session_id,
                "tool_call_requested",
                {
                    "capability_name": capability_name,
                    "arguments": arguments,
                },
                source=source,
            )

        result = self.local_hands.execute(capability, arguments)
        result.latency_ms = int((time.time() - start) * 1000)
        result.capability_name = capability_name

        if session_id:
            session_event_store.append_event_sync(
                session_id,
                "tool_call_completed" if result.success else "tool_call_blocked",
                {
                    "capability_name": capability_name,
                    "success": result.success,
                    "error": result.error,
                    "latency_ms": result.latency_ms,
                },
                source=source,
            )

        return result

    def execute_mcp(
        self,
        capability_name: str,
        arguments: Dict[str, Any],
        *,
        session_context: Dict[str, Any],
        session_id: str = "",
        source: str = "mcp_tool",
    ) -> CapabilityResult:
        start = time.time()
        if session_id:
            session_event_store.append_event_sync(
                session_id,
                "tool_call_requested",
                {
                    "capability_name": capability_name,
                    "arguments": arguments,
                    "transport": "mcp",
                },
                source=source,
            )

        result = self.mcp_hands.execute(capability_name, arguments, session_context)
        result.latency_ms = int((time.time() - start) * 1000)
        result.capability_name = capability_name

        if session_id:
            session_event_store.append_event_sync(
                session_id,
                "tool_call_completed" if result.success else "tool_call_blocked",
                {
                    "capability_name": capability_name,
                    "success": result.success,
                    "error": result.error,
                    "latency_ms": result.latency_ms,
                    "transport": "mcp",
                },
                source=source,
            )

        return result


capability_executor = CapabilityExecutor()
