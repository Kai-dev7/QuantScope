from tradingagents.skills import run_quality_gates


def test_quality_gates_warning_status_for_missing_risk_disclosure():
    result = run_quality_gates(
        {
            "summary": "这是一个足够长的摘要，用于通过完整性检查。",
            "recommendation": "建议继续观察后再决定。",
            "reports": {"market": "ok"},
            "detailed_analysis": {"market": "ok"},
            "risk_level": "",
            "decision": {"target_price": 12.3},
        },
        ["report_completeness_check", "risk_disclosure_check", "target_price_sanity_check"],
    )

    assert result["passed"] is True
    assert result["status"] == "warning"
    assert result["degrade_to"] == "completed_with_warnings"
    assert "risk_disclosure_check" in result["failed_gates"]


def test_quality_gates_block_on_report_completeness_failure():
    result = run_quality_gates(
        {
            "summary": "短",
            "recommendation": "",
            "reports": {},
            "detailed_analysis": {},
            "decision": {},
        },
        ["report_completeness_check"],
    )

    assert result["passed"] is False
    assert result["status"] == "failed"
    assert result["blocking_failed"] is True
    assert result["degrade_to"] == "needs_regeneration"
