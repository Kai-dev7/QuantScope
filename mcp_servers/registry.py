from __future__ import annotations

from contextlib import AsyncExitStack

from fastapi import FastAPI

from .config_server import server as config_server
from .docs_server import server as docs_server
from .reports_server import server as reports_server
from .sessions_server import server as sessions_server


def get_mcp_servers():
    return [
        reports_server,
        sessions_server,
        config_server,
        docs_server,
    ]


def mount_mcp_servers(app: FastAPI) -> None:
    app.mount("/mcp/reports", reports_server.streamable_http_app())
    app.mount("/mcp/sessions", sessions_server.streamable_http_app())
    app.mount("/mcp/config", config_server.streamable_http_app())
    app.mount("/mcp/docs", docs_server.streamable_http_app())


async def start_mcp_servers() -> AsyncExitStack:
    stack = AsyncExitStack()
    for server in get_mcp_servers():
        await stack.enter_async_context(server.session_manager.run())
    return stack
