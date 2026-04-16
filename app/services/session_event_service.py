"""
轻量级分析会话事件存储。

目标不是完整工作流恢复，而是先将关键运行事件持久化到 Redis，
把 agent 执行从“只有日志”提升为“可审计的 session event stream”。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.redis_client import get_redis_service


class SessionEventService:
    """Append-only session event store backed by Redis list."""

    SESSION_EVENTS_KEY = "analysis_session:{session_id}:events"
    SESSION_SUMMARY_KEY = "analysis_session:{session_id}:summary"
    DEFAULT_TTL_SECONDS = 7 * 24 * 3600

    async def append_event(
        self,
        session_id: str,
        event_type: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        redis_service = get_redis_service()
        event = {
            "session_id": session_id,
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "payload": payload or {},
        }
        event_key = self.SESSION_EVENTS_KEY.format(session_id=session_id)
        await redis_service.add_to_queue(event_key, event)
        await redis_service.redis.expire(event_key, self.DEFAULT_TTL_SECONDS)
        return event

    async def update_summary(
        self,
        session_id: str,
        summary: Dict[str, Any],
    ) -> None:
        redis_service = get_redis_service()
        summary_key = self.SESSION_SUMMARY_KEY.format(session_id=session_id)
        await redis_service.set_json(summary_key, summary, ttl=self.DEFAULT_TTL_SECONDS)

    async def get_events(self, session_id: str) -> List[Dict[str, Any]]:
        redis_service = get_redis_service()
        event_key = self.SESSION_EVENTS_KEY.format(session_id=session_id)
        raw_events = await redis_service.redis.lrange(event_key, 0, -1)

        events: List[Dict[str, Any]] = []
        for item in raw_events:
            try:
                import json

                events.append(json.loads(item))
            except Exception:
                continue
        return events


session_event_service = SessionEventService()

