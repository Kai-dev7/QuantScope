from __future__ import annotations

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.server import TransportSecuritySettings

from app.core.database import get_mongo_db_sync

_transport_security = TransportSecuritySettings(
    enable_dns_rebinding_protection=True,
    allowed_hosts=["127.0.0.1:*", "localhost:*", "[::1]:*", "host.docker.internal:*", "backend:*", "quantscope-backend:*"],
    allowed_origins=["http://127.0.0.1:*", "http://localhost:*", "http://[::1]:*", "http://host.docker.internal:*", "http://backend:*", "http://quantscope-backend:*"],
)

server = FastMCP(name="reports-server", stateless_http=True, transport_security=_transport_security)


@server.tool(name="list_reports")
def list_reports(limit: int = 10) -> dict:
    db = get_mongo_db_sync()
    docs = list(
        db.analysis_reports.find({}, {"_id": 0, "analysis_id": 1, "stock_symbol": 1, "summary": 1})
        .sort("created_at", -1)
        .limit(int(limit))
    )
    return {"reports": docs, "count": len(docs)}
