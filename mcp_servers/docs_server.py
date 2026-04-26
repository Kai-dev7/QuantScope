from __future__ import annotations

from pathlib import Path

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.server import TransportSecuritySettings

_transport_security = TransportSecuritySettings(
    enable_dns_rebinding_protection=True,
    allowed_hosts=["127.0.0.1:*", "localhost:*", "[::1]:*", "host.docker.internal:*", "backend:*", "quantscope-backend:*"],
    allowed_origins=["http://127.0.0.1:*", "http://localhost:*", "http://[::1]:*", "http://host.docker.internal:*", "http://backend:*", "http://quantscope-backend:*"],
)

server = FastMCP(name="docs-server", stateless_http=True, transport_security=_transport_security)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@server.tool(name="read_architecture_doc")
def read_architecture_doc() -> dict:
    path = PROJECT_ROOT / "docs" / "architecture" / "AGENT_RUNTIME_MODERNIZATION_PLAN.md"
    content = path.read_text(encoding="utf-8")
    return {"path": str(path), "content": content[:12000]}
