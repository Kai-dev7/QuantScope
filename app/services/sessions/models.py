from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


def utcnow_iso() -> str:
    return datetime.utcnow().isoformat()


@dataclass
class SessionEvent:
    session_id: str
    seq: int
    event_type: str
    timestamp: str = field(default_factory=utcnow_iso)
    payload: Dict[str, Any] = field(default_factory=dict)
    node_name: str = ""
    source: str = "runtime"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SessionSummary:
    session_id: str
    task_id: str = ""
    user_id: str = ""
    status: str = "running"
    skill_name: str = ""
    skill_version: Optional[int] = None
    analysis_context: Dict[str, Any] = field(default_factory=dict)
    last_event_seq: int = 0
    latest_checkpoint_id: str = ""
    started_at: str = field(default_factory=utcnow_iso)
    updated_at: str = field(default_factory=utcnow_iso)
    completed_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SessionCheckpoint:
    session_id: str
    checkpoint_id: str
    created_at: str = field(default_factory=utcnow_iso)
    state_summary: Dict[str, Any] = field(default_factory=dict)
    recoverable_state: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
