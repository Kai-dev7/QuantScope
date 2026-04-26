from app.services.capabilities.executor import CapabilityExecutor


def test_execute_mcp_uses_mcp_hands_and_marks_transport():
    executor = CapabilityExecutor()

    class DummyMCPHands:
        def execute(self, capability_name, arguments, session_context):
            from app.services.capabilities.models import CapabilityResult

            return CapabilityResult(
                success=True,
                capability_name=capability_name,
                result={
                    "arguments": arguments,
                    "server_url": session_context.get("server_url"),
                },
            )

    executor.mcp_hands = DummyMCPHands()
    result = executor.execute_mcp(
        "list_sessions",
        {"limit": 1},
        session_context={"server_url": "http://127.0.0.1:8000/mcp/sessions/mcp"},
        session_id="",
    )

    assert result.success is True
    assert result.result["arguments"]["limit"] == 1
    assert "server_url" in result.result
