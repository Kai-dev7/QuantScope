from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.routers.auth_db import get_current_user
from app.services.sessions import session_event_store, session_recovery_service

router = APIRouter()


@router.get("/sessions/{session_id}")
async def get_session_detail(
    session_id: str,
    user: dict = Depends(get_current_user),
):
    summary = await session_event_store.get_summary(session_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Session not found")

    events = await session_event_store.get_events(session_id)
    return {
        "success": True,
        "data": {
            "session": summary,
            "events": events,
            "viewer": user.get("username"),
        },
        "message": "Session detail loaded",
    }


@router.get("/sessions/{session_id}/recovery")
async def get_session_recovery_payload(
    session_id: str,
    user: dict = Depends(get_current_user),
):
    payload = await session_recovery_service.get_recovery_payload(session_id)
    if not payload.get("session"):
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "success": True,
        "data": payload,
        "message": f"Recovery payload loaded for {user.get('username')}",
    }


@router.get("/sessions")
async def list_sessions(
    task_id: str = Query(default=""),
    status: str = Query(default=""),
    limit: int = Query(default=20, ge=1, le=100),
    user: dict = Depends(get_current_user),
):
    sessions = await session_event_store.list_sessions(
        task_id=task_id,
        user_id=str(user.get("id", "")),
        status=status,
        limit=limit,
    )
    return {
        "success": True,
        "data": sessions,
        "message": "Sessions loaded",
    }
