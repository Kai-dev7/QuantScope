from __future__ import annotations

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.server import TransportSecuritySettings

from app.core.database import get_mongo_db_sync

_transport_security = TransportSecuritySettings(
    enable_dns_rebinding_protection=True,
    allowed_hosts=["127.0.0.1:*", "localhost:*", "[::1]:*", "host.docker.internal:*", "backend:*", "quantscope-backend:*"],
    allowed_origins=["http://127.0.0.1:*", "http://localhost:*", "http://[::1]:*", "http://host.docker.internal:*", "http://backend:*", "http://quantscope-backend:*"],
)

server = FastMCP(name="config-server", stateless_http=True, transport_security=_transport_security)


@server.tool(name="get_active_system_config")
def get_active_system_config() -> dict:
    db = get_mongo_db_sync()
    doc = db.system_configs.find_one({"is_active": True}, {"_id": 0}, sort=[("version", -1)])
    return {"config": doc or {}}
