from __future__ import annotations

from typing import Any, Dict, Optional

from app.core.database import get_mongo_db, get_mongo_db_sync

from .models import SessionCheckpoint


class SessionCheckpointStore:
    def __init__(self) -> None:
        self._collection_name = "analysis_session_checkpoints"

    async def save_checkpoint(self, checkpoint: SessionCheckpoint | Dict[str, Any]) -> Dict[str, Any]:
        doc = checkpoint.to_dict() if isinstance(checkpoint, SessionCheckpoint) else dict(checkpoint)
        db = get_mongo_db()
        await db[self._collection_name].insert_one(doc)
        await db["analysis_sessions"].update_one(
            {"session_id": doc["session_id"]},
            {"$set": {"latest_checkpoint_id": doc["checkpoint_id"], "updated_at": doc["created_at"]}},
            upsert=True,
        )
        return doc

    def save_checkpoint_sync(self, checkpoint: SessionCheckpoint | Dict[str, Any]) -> Dict[str, Any]:
        doc = checkpoint.to_dict() if isinstance(checkpoint, SessionCheckpoint) else dict(checkpoint)
        db = get_mongo_db_sync()
        db[self._collection_name].insert_one(doc)
        db["analysis_sessions"].update_one(
            {"session_id": doc["session_id"]},
            {"$set": {"latest_checkpoint_id": doc["checkpoint_id"], "updated_at": doc["created_at"]}},
            upsert=True,
        )
        return doc

    async def get_latest_checkpoint(self, session_id: str) -> Optional[Dict[str, Any]]:
        try:
            db = get_mongo_db()
            return await db[self._collection_name].find_one(
                {"session_id": session_id},
                {"_id": 0},
                sort=[("created_at", -1)],
            )
        except RuntimeError:
            db = get_mongo_db_sync()
            return db[self._collection_name].find_one(
                {"session_id": session_id},
                {"_id": 0},
                sort=[("created_at", -1)],
            )


session_checkpoint_store = SessionCheckpointStore()
