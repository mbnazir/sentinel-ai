from datetime import date

from app.analytics.behavior.services.session_fact_builder import SessionFactBuilder
from app.scans.domain.scan_models import SessionScanResult


def test_session_fact_builder_maps_scan_result() -> None:
    result = SessionScanResult("LS1", 75, "high_risk", 4)

    fact = SessionFactBuilder().from_scan_result(
        result=result,
        agent_external_id="A1",
        supervisor_external_id="S1",
        shift_date=date(2026, 7, 1),
    )

    assert fact.login_session_external_id == "LS1"
    assert fact.agent_external_id == "A1"
    assert fact.risk_score == 75
    assert fact.rule_count == 4
