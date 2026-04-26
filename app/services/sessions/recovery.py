from __future__ import annotations

from typing import Any, Dict, Optional

from .checkpoint_store import session_checkpoint_store
from .event_store import session_event_store


class SessionRecoveryService:
    async def get_recovery_payload(self, session_id: str) -> Dict[str, Any]:
        summary = await session_event_store.get_summary(session_id)
        checkpoint = await session_checkpoint_store.get_latest_checkpoint(session_id)
        after_seq = int((checkpoint or {}).get("state_summary", {}).get("last_event_seq", 0))
        events = await session_event_store.get_events(session_id, after_seq=after_seq)
        return {
            "session": summary,
            "checkpoint": checkpoint,
            "events_after_checkpoint": events,
        }


session_recovery_service = SessionRecoveryService()
