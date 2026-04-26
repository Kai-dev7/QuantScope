from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.routers.auth_db import get_current_user
from app.services.sessions import session_event_store

router = APIRouter()


@router.get("/quality/sessions/{session_id}")
async def get_session_quality_audit(
    session_id: str,
    user: dict = Depends(get_current_user),
):
    summary = await session_event_store.get_summary(session_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Session not found")

    events = await session_event_store.get_events(session_id)
    judge_events = [event for event in events if event.get("event_type") == "judge_evaluated"]
    quality_events = [event for event in events if event.get("event_type") == "quality_gate_evaluated"]

    latest_quality = quality_events[-1]["payload"] if quality_events else {}
    return {
        "success": True,
        "data": {
            "session": summary,
            "judge_events": judge_events,
            "quality_gate_events": quality_events,
            "latest_quality_status": latest_quality.get("status", "unknown"),
            "viewer": user.get("username"),
        },
        "message": "Quality audit loaded",
    }
