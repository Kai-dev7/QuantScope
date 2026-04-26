from __future__ import annotations

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.server import TransportSecuritySettings

from app.core.database import get_mongo_db_sync

_transport_security = TransportSecuritySettings(
    enable_dns_rebinding_protection=True,
    allowed_hosts=["127.0.0.1:*", "localhost:*", "[::1]:*", "host.docker.internal:*", "backend:*", "quantscope-backend:*"],
    allowed_origins=["http://127.0.0.1:*", "http://localhost:*", "http://[::1]:*", "http://host.docker.internal:*", "http://backend:*", "http://quantscope-backend:*"],
)

server = FastMCP(name="sessions-server", stateless_http=True, transport_security=_transport_security)


@server.tool(name="list_sessions")
def list_sessions(limit: int = 10) -> dict:
    db = get_mongo_db_sync()
    docs = list(
        db.analysis_sessions.find({}, {"_id": 0})
        .sort("updated_at", -1)
        .limit(int(limit))
    )
    return {"sessions": docs, "count": len(docs)}


@server.tool(name="get_session_recovery")
def get_session_recovery(session_id: str) -> dict:
    db = get_mongo_db_sync()
    session = db.analysis_sessions.find_one({"session_id": session_id}, {"_id": 0})
    checkpoint = db.analysis_session_checkpoints.find_one(
        {"session_id": session_id},
        {"_id": 0},
        sort=[("created_at", -1)],
    )
    after_seq = int((checkpoint or {}).get("state_summary", {}).get("last_event_seq", 0))
    events = list(
        db.analysis_session_events.find(
            {"session_id": session_id, "seq": {"$gt": after_seq}},
            {"_id": 0},
        ).sort("seq", 1)
    )
    return {
        "session": session,
        "checkpoint": checkpoint,
        "events_after_checkpoint": events,
    }
