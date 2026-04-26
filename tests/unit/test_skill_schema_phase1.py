from app.models.analysis import AnalysisParameters
from tradingagents.skills import (
    SkillMatchContext,
    SkillSelector,
    get_default_skill_registry,
    project_batch_skill_parameters,
)


def test_skill_selector_matches_single_stock_a_share_skill():
    selector = SkillSelector(get_default_skill_registry())

    selected = selector.select_for_context(
        SkillMatchContext(
            task_type="single_stock_analysis",
            market_scope="A股",
            research_depth="标准",
        )
    )

    assert selected is not None
    assert selected.name == "standard-a-share-analysis"


def test_project_batch_skill_parameters_creates_isolated_copy():
    registry = get_default_skill_registry()
    batch_skill = registry.get("batch-low-cost-screening")
    original = AnalysisParameters(
        market_type="A股",
        research_depth="基础",
        selected_analysts=["market", "fundamentals", "news", "social"],
    )

    projected = project_batch_skill_parameters(original, batch_skill)

    assert projected is not None
    assert projected is not original
    assert projected.selected_analysts == ["market", "fundamentals"]
    assert projected.research_depth == "快速"

    # Ensure original request parameters are not mutated across batch subtasks.
    assert original.selected_analysts == ["market", "fundamentals", "news", "social"]
    assert original.research_depth == "基础"


def test_project_batch_skill_parameters_without_skill_keeps_values():
    original = AnalysisParameters(
        market_type="A股",
        research_depth="标准",
        selected_analysts=["market", "news"],
    )

    projected = project_batch_skill_parameters(original, None)

    assert projected is not None
    assert projected is not original
    assert projected.selected_analysts == ["market", "news"]
    assert projected.research_depth == "标准"


def test_session_runtime_sync_start_and_checkpoint_ordering():
    from app.services.sessions.models import SessionSummary

    summary = SessionSummary(
        session_id="session-1",
        task_id="task-1",
        user_id="user-1",
        skill_name="skill-a",
        skill_version=1,
    )

    db_updates = []
    appended_events = []
    checkpoint_saves = []

    class DummyDBCollection:
        def __init__(self, name):
            self.name = name

        def update_one(self, query, update, upsert=False):
            db_updates.append((self.name, query, update, upsert))

    class DummyDB:
        def __getitem__(self, name):
            return DummyDBCollection(name)

    class DummyEventStore:
        def append_event_sync(self, session_id, event_type, payload=None, **kwargs):
            seq = len(appended_events) + 1
            appended_events.append((session_id, event_type, payload or {}, kwargs))
            return {"seq": seq}

    class DummyCheckpointStore:
        def save_checkpoint_sync(self, checkpoint):
            checkpoint_saves.append(checkpoint.to_dict() if hasattr(checkpoint, "to_dict") else checkpoint)
            return checkpoint_saves[-1]

    from app.services.sessions import runtime as runtime_module

    original_db_sync = runtime_module.get_mongo_db_sync if hasattr(runtime_module, "get_mongo_db_sync") else None
    original_event_store = runtime_module.session_event_store
    original_checkpoint_store = runtime_module.session_checkpoint_store
    original_session_summary = runtime_module.SessionSummary

    try:
        runtime_module.get_mongo_db_sync = lambda: DummyDB()
        runtime_module.session_event_store = DummyEventStore()
        runtime_module.session_checkpoint_store = DummyCheckpointStore()
        runtime_module.SessionSummary = lambda **kwargs: summary

        result = runtime_module.SessionRuntimeService().start_session_sync(
            "session-1",
            task_id="task-1",
            user_id="user-1",
            skill_name="skill-a",
            skill_version=1,
        )
        assert appended_events[0][1] == "session_started"
        assert appended_events[1][1] == "skill_selected"
        assert result["last_event_seq"] == 2

        checkpoint_doc = runtime_module.SessionRuntimeService().checkpoint_sync(
            "session-1",
            state_summary={"node_name": "Trader", "last_event_seq": 9},
            recoverable_state={"ok": True},
            checkpoint_id="cp-1",
            created_at="2026-04-26T14:20:00",
        )
        assert checkpoint_doc["state_summary"]["last_event_seq"] == 9
        assert appended_events[-1][1] == "session_checkpointed"
    finally:
        if original_db_sync is not None:
            runtime_module.get_mongo_db_sync = original_db_sync
        runtime_module.session_event_store = original_event_store
        runtime_module.session_checkpoint_store = original_checkpoint_store
        runtime_module.SessionSummary = original_session_summary
