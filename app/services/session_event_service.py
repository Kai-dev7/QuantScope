"""
Backward-compatible session event facade.

This module is kept to avoid breaking older imports while the new session
store/recovery runtime is rolled out incrementally.
"""

from __future__ import annotations

from app.services.sessions import session_event_store


class SessionEventServiceCompat:
    async def append_event(self, session_id, event_type, payload=None):
        return await session_event_store.append_event(session_id, event_type, payload)

    async def update_summary(self, session_id, summary):
        return await session_event_store.upsert_summary({"session_id": session_id, **(summary or {})})

    async def get_events(self, session_id):
        return await session_event_store.get_events(session_id)


session_event_service = SessionEventServiceCompat()
