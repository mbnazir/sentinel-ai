"""Exercise QF-001 verification through the actual ingestion snapshot mapper."""

from datetime import UTC, date, datetime, timedelta
from uuid import uuid4

import pytest

from app.application.ingestion import _session_row
from app.application.normalized import NormalizedLoginSession
from app.rules.historical_comparison import evaluate_manager_decision_reversals_detailed
from app.workers.pipeline import observation_from_session_snapshot


def snapshot(*, status_id=2, supervisor_status_id=4, observed_at=None, **values):
    session = NormalizedLoginSession(
        source_system="quartz",
        source_session_id="synthetic-session",
        agent_id="synthetic-agent",
        shift_date=date(2026, 8, 26),
        start_at=datetime(2026, 8, 26, 8, tzinfo=UTC),
        ready_for_payroll=True,
        status_id=status_id,
        supervisor_status_id=supervisor_status_id,
        **values,
    )
    row = _session_row(uuid4(), session)
    row.id = uuid4()
    row.observed_at = observed_at or datetime(2026, 8, 27, tzinfo=UTC)
    return row


@pytest.mark.parametrize("client", [
    {},
    {"primary_client_id": 123},
    {"primary_client_name": "Synthetic client"},
    {"primary_client_id": 123, "primary_client_name": "Synthetic client"},
])
def test_ingested_client_evidence_verifies(client):
    assert observation_from_session_snapshot(snapshot(**client)).content_hash_verified


@pytest.mark.parametrize("field,value", [
    ("primary_client_id", 999),
    ("primary_client_name", "Changed client"),
    ("status_id", 5),
    ("supervisor_status_id", 5),
    ("metadata_json", {"changed": True}),
])
def test_changed_evidence_is_still_rejected(field, value):
    row = snapshot(primary_client_id=123, primary_client_name="Synthetic client")
    setattr(row, field, value)
    observation = observation_from_session_snapshot(row)
    assert not observation.content_hash_verified
    result = evaluate_manager_decision_reversals_detailed(
        [observation], [], earlier_run_id=row.ingestion_run_id, later_run_id=uuid4(),
    )
    assert result.findings == ()
    assert result.excluded_record_counts["content_hash_mismatch_records"] == 1


def test_payroll_ready_reversal_with_client_evidence_produces_finding():
    earlier = snapshot(primary_client_id=123, primary_client_name="Synthetic client")
    later = snapshot(
        supervisor_status_id=5, observed_at=earlier.observed_at + timedelta(days=1),
        primary_client_id=123, primary_client_name="Synthetic client",
    )
    result = evaluate_manager_decision_reversals_detailed(
        [observation_from_session_snapshot(earlier)],
        [observation_from_session_snapshot(later)],
    )
    assert result.matched_pairs_count == 1
    assert len(result.findings) == 1
    assert result.findings[0].metadata["transition"] == "4->5"


@pytest.mark.parametrize("session_id,status_id,old_decision,new_decision", [
    ("180660384", 2, 4, 5),
    ("180667650", 2, 5, 4),
    ("180689901", 2, 4, 5),
    ("180690354", 2, 4, 5),
    ("180691869", 1, 4, 5),
])
def test_reported_status_pairs_use_manager_decision_column(
    session_id, status_id, old_decision, new_decision,
):
    earlier = snapshot(status_id=status_id, supervisor_status_id=old_decision)
    later = snapshot(
        status_id=status_id, supervisor_status_id=new_decision,
        observed_at=earlier.observed_at + timedelta(days=1),
    )
    # Session IDs identify the reported cases; all other identity data is synthetic.
    old = observation_from_session_snapshot(earlier)
    new = observation_from_session_snapshot(later)
    result = evaluate_manager_decision_reversals_detailed([old], [new])
    assert len(result.findings) == 1, session_id
    evidence = result.findings[0].metadata
    assert evidence["transition"] == f"{old_decision}->{new_decision}"
    assert evidence["decision_field"] == "supervisor_status_id"
    assert evidence["earlier"]["status_id"] == status_id
    assert evidence["earlier"]["supervisor_status_id"] == old_decision
    assert evidence["later"]["supervisor_status_id"] == new_decision


@pytest.mark.parametrize("old_decision,new_decision", [(4, 4), (None, None), (3, 6)])
def test_session_status_change_alone_cannot_trigger_manager_reversal(
    old_decision, new_decision,
):
    earlier = snapshot(status_id=4, supervisor_status_id=old_decision)
    later = snapshot(
        status_id=5, supervisor_status_id=new_decision,
        observed_at=earlier.observed_at + timedelta(days=1),
    )
    result = evaluate_manager_decision_reversals_detailed(
        [observation_from_session_snapshot(earlier)],
        [observation_from_session_snapshot(later)],
    )
    assert result.findings == ()
