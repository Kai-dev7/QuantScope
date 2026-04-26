from __future__ import annotations

import anyio
from typing import Any, Dict

from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from .models import CapabilityResult


class MCPHands:
    async def _execute_async(self, server_url: str, capability_name: str, arguments: Dict[str, Any]) -> CapabilityResult:
        async with streamablehttp_client(server_url) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool(capability_name, arguments)
                payload = getattr(result, "content", result)
                if isinstance(payload, list):
                    normalized = []
                    for item in payload:
                        text = getattr(item, "text", None)
                        normalized.append(text if text is not None else str(item))
                    payload = normalized
                return CapabilityResult(
                    success=True,
                    capability_name=capability_name,
                    result=payload,
                    metadata={"server_url": server_url},
                )

    def execute(self, capability_name: str, arguments: Dict[str, Any], session_context: Dict[str, Any]) -> CapabilityResult:
        server_url = str((session_context or {}).get("server_url", "") or "")
        if not server_url:
            return CapabilityResult(
                success=False,
                capability_name=capability_name,
                error="Missing MCP server_url in session_context",
                metadata={"session_context": session_context},
            )
        try:
            return anyio.run(self._execute_async, server_url, capability_name, arguments)
        except Exception as exc:
            return CapabilityResult(
                success=False,
                capability_name=capability_name,
                error=str(exc),
                metadata={"server_url": server_url, "session_context": session_context},
            )
