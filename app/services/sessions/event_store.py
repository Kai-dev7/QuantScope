from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.database import get_mongo_db, get_mongo_db_sync
from app.core.redis_client import get_redis_service
from pymongo import ReturnDocument

from .models import SessionEvent, SessionSummary


class SessionEventStore:
    SESSION_EVENTS_KEY = "analysis_session:{session_id}:events"
    SESSION_SUMMARY_KEY = "analysis_session:{session_id}:summary"
    SESSION_SEQ_KEY = "analysis_session:{session_id}:seq"
    DEFAULT_TTL_SECONDS = 7 * 24 * 3600

    def __init__(self) -> None:
        self._events_collection_name = "analysis_session_events"
        self._sessions_collection_name = "analysis_sessions"
        self._counters_collection_name = "_runtime_counters"

    def _get_redis_service_safe(self):
        try:
            return get_redis_service()
        except RuntimeError:
            return None

    async def _allocate_seq_async(self, session_id: str) -> int:
        redis_service = self._get_redis_service_safe()
        if redis_service is not None:
            seq = await redis_service.redis.incr(self.SESSION_SEQ_KEY.format(session_id=session_id))
            await redis_service.redis.expire(
                self.SESSION_SEQ_KEY.format(session_id=session_id),
                self.DEFAULT_TTL_SECONDS,
            )
            return int(seq)

        db = get_mongo_db()
        seq_doc = await db[self._counters_collection_name].find_one_and_update(
            {"_id": f"analysis_session_seq:{session_id}"},
            {"$inc": {"value": 1}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return int((seq_doc or {}).get("value", 1))

    async def append_event(
        self,
        session_id: str,
        event_type: str,
        payload: Optional[Dict[str, Any]] = None,
        *,
        node_name: str = "",
        source: str = "runtime",
    ) -> Dict[str, Any]:
        seq = await self._allocate_seq_async(session_id)

        event = SessionEvent(
            session_id=session_id,
            seq=int(seq),
            event_type=event_type,
            payload=payload or {},
            node_name=node_name,
            source=source,
        )
        event_dict = event.to_dict()

        event_key = self.SESSION_EVENTS_KEY.format(session_id=session_id)
        redis_service = self._get_redis_service_safe()
        if redis_service is not None:
            await redis_service.add_to_queue(event_key, event_dict)
            await redis_service.redis.expire(event_key, self.DEFAULT_TTL_SECONDS)

        db = get_mongo_db()
        await db[self._events_collection_name].insert_one(event_dict)
        await db[self._sessions_collection_name].update_one(
            {"session_id": session_id},
            {
                "$set": {
                    "last_event_seq": event.seq,
                    "updated_at": datetime.utcnow().isoformat(),
                }
            },
            upsert=True,
        )
        return event_dict

    def append_event_sync(
        self,
        session_id: str,
        event_type: str,
        payload: Optional[Dict[str, Any]] = None,
        *,
        node_name: str = "",
        source: str = "runtime",
    ) -> Dict[str, Any]:
        db = get_mongo_db_sync()
        counters = db[self._counters_collection_name]
        seq_doc = counters.find_one_and_update(
            {"_id": f"analysis_session_seq:{session_id}"},
            {"$inc": {"value": 1}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        seq = int((seq_doc or {}).get("value", 1))

        event = SessionEvent(
            session_id=session_id,
            seq=seq,
            event_type=event_type,
            payload=payload or {},
            node_name=node_name,
            source=source,
        )
        event_dict = event.to_dict()
        db[self._events_collection_name].insert_one(event_dict)
        db[self._sessions_collection_name].update_one(
            {"session_id": session_id},
            {
                "$set": {
                    "last_event_seq": seq,
                    "updated_at": datetime.utcnow().isoformat(),
                }
            },
            upsert=True,
        )
        return event_dict

    async def upsert_summary(self, summary: SessionSummary | Dict[str, Any]) -> Dict[str, Any]:
        summary_dict = summary.to_dict() if isinstance(summary, SessionSummary) else dict(summary)
        summary_dict["updated_at"] = datetime.utcnow().isoformat()

        redis_service = self._get_redis_service_safe()
        if redis_service is not None:
            summary_key = self.SESSION_SUMMARY_KEY.format(session_id=summary_dict["session_id"])
            await redis_service.set_json(summary_key, summary_dict, ttl=self.DEFAULT_TTL_SECONDS)

        db = get_mongo_db()
        await db[self._sessions_collection_name].update_one(
            {"session_id": summary_dict["session_id"]},
            {"$set": summary_dict},
            upsert=True,
        )
        return summary_dict

    async def get_events(self, session_id: str, after_seq: int = 0) -> List[Dict[str, Any]]:
        query = {"session_id": session_id, "seq": {"$gt": int(after_seq)}}
        try:
            db = get_mongo_db()
            cursor = db[self._events_collection_name].find(query, {"_id": 0}).sort("seq", 1)
            return [doc async for doc in cursor]
        except RuntimeError:
            db = get_mongo_db_sync()
            return list(db[self._events_collection_name].find(query, {"_id": 0}).sort("seq", 1))

    async def get_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        redis_service = self._get_redis_service_safe()
        if redis_service is not None:
            summary_key = self.SESSION_SUMMARY_KEY.format(session_id=session_id)
            cached = await redis_service.get_json(summary_key)
            if cached:
                return cached

        try:
            db = get_mongo_db()
            return await db[self._sessions_collection_name].find_one({"session_id": session_id}, {"_id": 0})
        except RuntimeError:
            db = get_mongo_db_sync()
            return db[self._sessions_collection_name].find_one({"session_id": session_id}, {"_id": 0})

    async def list_sessions(
        self,
        *,
        task_id: str = "",
        user_id: str = "",
        status: str = "",
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        query: Dict[str, Any] = {}
        if task_id:
            query["task_id"] = task_id
        if user_id:
            query["user_id"] = user_id
        if status:
            query["status"] = status

        try:
            db = get_mongo_db()
            cursor = db[self._sessions_collection_name].find(query, {"_id": 0}).sort("updated_at", -1).limit(int(limit))
            return [doc async for doc in cursor]
        except RuntimeError:
            db = get_mongo_db_sync()
            return list(
                db[self._sessions_collection_name]
                .find(query, {"_id": 0})
                .sort("updated_at", -1)
                .limit(int(limit))
            )


session_event_store = SessionEventStore()
