from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from app.core.database import get_mongo_db_sync

from .checkpoint_store import session_checkpoint_store
from .event_store import session_event_store
from .models import SessionCheckpoint, SessionSummary


class SessionRuntimeService:
    @staticmethod
    def _resolve_completion_event_type(status: str) -> str:
        normalized = str(status or "").strip().lower()
        if normalized in {"failed", "needs_regeneration", "requires_review"}:
            return "session_failed"
        return "session_completed"

    async def start_session(
        self,
        session_id: str,
        *,
        task_id: str = "",
        user_id: str = "",
        skill_name: str = "",
        skill_version: int | None = None,
        analysis_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        summary = SessionSummary(
            session_id=session_id,
            task_id=task_id,
            user_id=user_id,
            status="running",
            skill_name=skill_name,
            skill_version=skill_version,
            analysis_context=analysis_context or {},
        )
        await session_event_store.upsert_summary(summary)
        await session_event_store.append_event(
            session_id,
            "session_started",
            {
                "task_id": task_id,
                "user_id": user_id,
                "skill_name": skill_name,
                "skill_version": skill_version,
                "analysis_context": analysis_context or {},
            },
            source="service",
        )
        if skill_name:
            await session_event_store.append_event(
                session_id,
                "skill_selected",
                {
                    "skill_name": skill_name,
                    "skill_version": skill_version,
                },
                source="service",
            )
        return summary.to_dict()

    def start_session_sync(
        self,
        session_id: str,
        *,
        task_id: str = "",
        user_id: str = "",
        skill_name: str = "",
        skill_version: int | None = None,
        analysis_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        summary = SessionSummary(
            session_id=session_id,
            task_id=task_id,
            user_id=user_id,
            status="running",
            skill_name=skill_name,
            skill_version=skill_version,
            analysis_context=analysis_context or {},
        )
        db_summary = summary.to_dict()
        db_summary["updated_at"] = datetime.utcnow().isoformat()
        db = get_mongo_db_sync()
        db["analysis_sessions"].update_one(
            {"session_id": session_id},
            {"$set": db_summary},
            upsert=True,
        )
        session_started_event = session_event_store.append_event_sync(
            session_id,
            "session_started",
            {
                "task_id": task_id,
                "user_id": user_id,
                "skill_name": skill_name,
                "skill_version": skill_version,
                "analysis_context": analysis_context or {},
            },
            source="service",
        )
        db_summary["last_event_seq"] = int(session_started_event.get("seq", 0))
        if skill_name:
            skill_selected_event = session_event_store.append_event_sync(
                session_id,
                "skill_selected",
                {
                    "skill_name": skill_name,
                    "skill_version": skill_version,
                },
                source="service",
            )
            db_summary["last_event_seq"] = int(skill_selected_event.get("seq", db_summary["last_event_seq"]))
        return db_summary

    async def checkpoint(
        self,
        session_id: str,
        *,
        recoverable_state: Dict[str, Any],
        state_summary: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        checkpoint = SessionCheckpoint(
            session_id=session_id,
            checkpoint_id=str(uuid.uuid4()),
            state_summary=state_summary or {},
            recoverable_state=recoverable_state,
        )
        doc = await session_checkpoint_store.save_checkpoint(checkpoint)
        await session_event_store.append_event(
            session_id,
            "session_checkpointed",
            {
                "checkpoint_id": checkpoint.checkpoint_id,
                "state_summary": checkpoint.state_summary,
            },
            source="runtime",
        )
        return doc

    def checkpoint_sync(
        self,
        session_id: str,
        *,
        recoverable_state: Dict[str, Any],
        state_summary: Optional[Dict[str, Any]] = None,
        checkpoint_id: Optional[str] = None,
        created_at: Optional[str] = None,
    ) -> Dict[str, Any]:
        checkpoint = SessionCheckpoint(
            session_id=session_id,
            checkpoint_id=checkpoint_id or str(uuid.uuid4()),
            created_at=created_at or datetime.utcnow().isoformat(),
            state_summary=state_summary or {},
            recoverable_state=recoverable_state,
        )
        doc = session_checkpoint_store.save_checkpoint_sync(checkpoint)
        session_event_store.append_event_sync(
            session_id,
            "session_checkpointed",
            {
                "checkpoint_id": checkpoint.checkpoint_id,
                "state_summary": checkpoint.state_summary,
            },
            source="runtime",
        )
        return doc

    async def complete_session(
        self,
        session_id: str,
        *,
        status: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        summary = await session_event_store.get_summary(session_id) or {"session_id": session_id}
        summary["status"] = status
        summary["completed_at"] = datetime.utcnow().isoformat()
        await session_event_store.upsert_summary(summary)
        await session_event_store.append_event(
            session_id,
            self._resolve_completion_event_type(status),
            payload or {},
            source="service",
        )

    def complete_session_sync(
        self,
        session_id: str,
        *,
        status: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        db = get_mongo_db_sync()
        db["analysis_sessions"].update_one(
            {"session_id": session_id},
            {
                "$set": {
                    "status": status,
                    "completed_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat(),
                }
            },
            upsert=True,
        )
        session_event_store.append_event_sync(
            session_id,
            self._resolve_completion_event_type(status),
            payload or {},
            source="service",
        )


session_runtime_service = SessionRuntimeService()
