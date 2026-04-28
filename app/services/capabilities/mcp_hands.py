from __future__ import annotations

import asyncio
import anyio
import threading
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

    async def execute_async(
        self,
        capability_name: str,
        arguments: Dict[str, Any],
        session_context: Dict[str, Any],
    ) -> CapabilityResult:
        server_url = str((session_context or {}).get("server_url", "") or "")
        if not server_url:
            return CapabilityResult(
                success=False,
                capability_name=capability_name,
                error="Missing MCP server_url in session_context",
                metadata={"session_context": session_context},
            )
        try:
            return await self._execute_async(server_url, capability_name, arguments)
        except Exception as exc:
            return CapabilityResult(
                success=False,
                capability_name=capability_name,
                error=str(exc),
                metadata={"server_url": server_url, "session_context": session_context},
            )

    def execute(self, capability_name: str, arguments: Dict[str, Any], session_context: Dict[str, Any]) -> CapabilityResult:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return anyio.run(self.execute_async, capability_name, arguments, session_context)

        result: CapabilityResult | None = None

        def _runner() -> None:
            nonlocal result
            result = anyio.run(self.execute_async, capability_name, arguments, session_context)

        thread = threading.Thread(target=_runner, daemon=True)
        thread.start()
        thread.join()
        return result or CapabilityResult(
            success=False,
            capability_name=capability_name,
            error="MCP execution did not return a result",
            metadata={"session_context": session_context},
        )
