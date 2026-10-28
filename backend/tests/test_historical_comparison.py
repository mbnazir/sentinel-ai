from dataclasses import replace
from datetime import UTC, date, datetime
import hashlib
from uuid import UUID

import pytest

from app.rules.historical_comparison import (
    ManagerDecisionObservation,
    evaluate_manager_decision_reversals,
    evaluate_manager_decision_reversals_detailed,
)
from app.rules.models import FindingCategory, RuleSeverity


EARLIER_RUN = UUID("a62525d0-3d22-4944-a4f3-5cc1540854f7")
LATER_RUN = UUID("026961c1-9442-4818-af5f-620c0be3d62f")
DETECTIONS = {
    "180660384": (4, 5),
    "180667650": (5, 4),
    "180689901": (4, 5),
    "180690354": (4, 5),
    "180691869": (4, 5),
}


def observation(
    session_id: str,
    *,
    run_id=EARLIER_RUN,
    status_id=4,
    observed_at=datetime(2026, 8, 26, tzinfo=UTC),
    ready=True,
    manager_action_at=None,
) -> ManagerDecisionObservation:
    return ManagerDecisionObservation(
        snapshot_id=f"snapshot-{run_id}-{session_id}",
        ingestion_run_id=run_id,
        source_system="quartz",
        source_session_id=session_id,
        status_id=status_id,
        ready_for_payroll=ready,
        observed_at=observed_at,
        manager_action_at=manager_action_at,
        agent_id="agent-1",
        shift_date=date(2026, 8, 25),
        content_hash=hashlib.sha256(f"{run_id}-{session_id}-{status_id}".encode()).hexdigest(),
    )


def pair(old_status: int, new_status: int, **kwargs):
    old = observation("session-1", status_id=old_status, **kwargs)
    new = observation(
        "session-1",
        run_id=LATER_RUN,
        status_id=new_status,
        observed_at=datetime(2026, 8, 27, tzinfo=UTC),
        **{key: value for key, value in kwargs.items() if key != "observed_at"},
    )
    return old, new


def test_five_historical_validation_sessions_produce_expected_findings():
    earlier = [observation(sid, status_id=old) for sid, (old, _) in DETECTIONS.items()]
    later = [
        observation(
            sid,
            run_id=LATER_RUN,
            status_id=new,
            observed_at=datetime(2026, 8, 27, tzinfo=UTC),
        )
        for sid, (_, new) in DETECTIONS.items()
    ]

    findings = evaluate_manager_decision_reversals(earlier, later)

    assert len(findings) == 5
    assert {f.source_session_id for f in findings} == set(DETECTIONS)
    assert all(f.rule_id == "QF-001" for f in findings)
    assert all(f.severity is RuleSeverity.MEDIUM for f in findings)
    assert all(f.category is FindingCategory.WORKFLOW for f in findings)
    assert {f.metadata["transition"] for f in findings} == {"4->5", "5->4"}


@pytest.mark.parametrize("status_id", [4, 5])
def test_no_finding_for_unchanged_decision(status_id):
    old, new = pair(status_id, status_id)
    assert evaluate_manager_decision_reversals([old], [new]) == ()


@pytest.mark.parametrize("earlier_ready,later_ready", [(False, True), (True, False), (False, False)])
def test_requires_payroll_ready_in_both_observations(earlier_ready, later_ready):
    old = observation("s", ready=earlier_ready)
    new = observation("s", run_id=LATER_RUN, status_id=5, ready=later_ready,
                      observed_at=datetime(2026, 8, 27, tzinfo=UTC))
    assert evaluate_manager_decision_reversals([old], [new]) == ()


def test_unmatched_session_is_ignored():
    old = observation("only-old")
    new = observation("only-new", run_id=LATER_RUN, status_id=5,
                      observed_at=datetime(2026, 8, 27, tzinfo=UTC))
    assert evaluate_manager_decision_reversals([old], [new]) == ()


def test_identical_run_ids_are_not_compared():
    old = observation("s", status_id=4)
    new = observation("s", status_id=5, observed_at=datetime(2026, 8, 27, tzinfo=UTC))
    assert evaluate_manager_decision_reversals([old], [new]) == ()


def test_finding_key_is_deterministic_across_repeated_evaluation():
    old, new = pair(4, 5)
    first = evaluate_manager_decision_reversals([old], [new])
    second = evaluate_manager_decision_reversals([old], [new])
    assert first == second
    assert first[0].metadata["finding_key"] == second[0].metadata["finding_key"]


def test_finding_preserves_both_observation_provenance_records():
    old, new = pair(4, 5)
    finding = evaluate_manager_decision_reversals([old], [new])[0]
    assert finding.metadata["earlier"] == {
        "snapshot_id": str(old.snapshot_id),
        "ingestion_run_id": str(EARLIER_RUN),
        "content_hash": old.content_hash,
        "observed_at": old.observed_at.isoformat(),
        "manager_action_at": None,
        "status_id": 4,
        "agent_id": "agent-1",
        "shift_date": "2026-08-25",
    }
    assert finding.metadata["later"]["snapshot_id"] == str(new.snapshot_id)
    assert finding.metadata["later"]["ingestion_run_id"] == str(LATER_RUN)
    assert finding.metadata["later"]["content_hash"] == new.content_hash


def test_observation_timestamps_must_be_chronological():
    old = observation("s", status_id=4, observed_at=datetime(2026, 8, 27, tzinfo=UTC))
    new = observation("s", run_id=LATER_RUN, status_id=5,
                      observed_at=datetime(2026, 8, 26, tzinfo=UTC))
    assert evaluate_manager_decision_reversals([old], [new]) == ()


def test_manager_action_before_later_observation_is_preserved_without_access_claim():
    manager_action = datetime(2026, 8, 25, tzinfo=UTC)
    old, new = pair(4, 5, manager_action_at=manager_action)
    finding = evaluate_manager_decision_reversals([old], [new])[0]
    assert finding.metadata["earlier"]["manager_action_at"] == manager_action.isoformat()
    assert finding.metadata["editor_identity"] == "UNVERIFIED"
    assert "unauthorized access" in finding.reason
    assert finding.metadata["financial_impact"] == "UNVERIFIED"


def test_ambiguous_duplicate_observation_is_not_arbitrarily_selected():
    old = observation("s", status_id=4)
    old_duplicate = observation("s", status_id=5)
    new = observation("s", run_id=LATER_RUN, status_id=5,
                      observed_at=datetime(2026, 8, 27, tzinfo=UTC))
    assert evaluate_manager_decision_reversals([old, old_duplicate], [new]) == ()


def test_source_system_is_part_of_session_identity():
    old = observation("s", status_id=4)
    new = observation("s", run_id=LATER_RUN, status_id=5, observed_at=datetime(2026, 8, 27, tzinfo=UTC))
    other_system = observation("s", run_id=LATER_RUN, status_id=5, observed_at=datetime(2026, 8, 27, tzinfo=UTC))
    other_system = replace(other_system, source_system="other")
    assert evaluate_manager_decision_reversals([old], [other_system]) == ()


def test_invalid_hash_and_duplicate_pairs_are_reported_as_exclusions():
    old = observation("s", status_id=4)
    invalid_hash = replace(old, source_session_id="bad-hash", content_hash="not-a-hash")
    duplicate = replace(old, snapshot_id="duplicate-snapshot")
    new = observation("s", run_id=LATER_RUN, status_id=5,
                      observed_at=datetime(2026, 8, 27, tzinfo=UTC))
    old_good = observation("good", status_id=4)
    new_good = observation("good", run_id=LATER_RUN, status_id=5,
                           observed_at=datetime(2026, 8, 27, tzinfo=UTC))
    result = evaluate_manager_decision_reversals_detailed(
        [old, invalid_hash, duplicate, old_good], [new, new_good]
    )
    assert [finding.source_session_id for finding in result.findings] == ["good"]
    assert result.excluded_record_counts["invalid_content_hash_records"] == 1
    # Both old versions and the corresponding later row are excluded as one
    # ambiguous three-record session identity.
    assert result.excluded_record_counts["ambiguous_duplicate_records"] == 3


def test_unmatched_snapshot_is_counted_without_deletion_interpretation():
    old = observation("present-earlier", status_id=4)
    new = observation("present-later", run_id=LATER_RUN, status_id=5,
                      observed_at=datetime(2026, 8, 27, tzinfo=UTC))
    result = evaluate_manager_decision_reversals_detailed([old], [new])
    assert result.findings == ()
    assert result.excluded_record_counts["unmatched_earlier_records"] == 1
    assert result.excluded_record_counts["unmatched_later_records"] == 1


def test_canonical_hash_mismatch_is_counted_and_excluded():
    old = replace(observation("s", status_id=4), content_hash_verified=False)
    new = observation(
        "s", run_id=LATER_RUN, status_id=5,
        observed_at=datetime(2026, 8, 27, tzinfo=UTC),
    )
    result = evaluate_manager_decision_reversals_detailed([old], [new])
    assert result.findings == ()
    assert result.excluded_record_counts["content_hash_mismatch_records"] == 1
    assert result.excluded_record_counts["unmatched_later_records"] == 1


@pytest.mark.parametrize(
    ("alter", "reason"),
    [
        (lambda row: replace(row, agent_id="different-agent"), "conflicting_agent_identity_pairs"),
        (lambda row: replace(row, observed_at=datetime(2026, 8, 25, tzinfo=UTC)), "non_chronological_pairs"),
    ],
)
def test_excluded_pair_diagnostic_identifies_the_session(alter, reason):
    old = observation("excluded-session", status_id=4)
    new = observation(
        "excluded-session", run_id=LATER_RUN, status_id=5,
        observed_at=datetime(2026, 8, 27, tzinfo=UTC),
    )
    result = evaluate_manager_decision_reversals_detailed([old], [alter(new)])
    assert result.matched_pairs_count == 1
    assert result.valid_comparisons_count == 0
    assert result.excluded_pair_session_ids[reason] == ("excluded-session",)


def test_all_date_comparison_and_requested_shift_date_are_distinct_scopes():
    other_day_old = replace(observation("other-day", status_id=4), shift_date=date(2026, 8, 25))
    other_day_new = replace(
        observation(
            "other-day", run_id=LATER_RUN, status_id=5,
            observed_at=datetime(2026, 8, 27, tzinfo=UTC),
        ),
        shift_date=date(2026, 8, 25),
    )
    target_old, target_new = pair(4, 5)
    all_dates = evaluate_manager_decision_reversals_detailed(
        [target_old, other_day_old], [target_new, other_day_new]
    )
    requested_day = evaluate_manager_decision_reversals_detailed(
        [target_old], [target_new]
    )
    assert all_dates.matched_pairs_count == 2
    assert len(all_dates.findings) == 2
    assert requested_day.matched_pairs_count == 1
    assert [finding.source_session_id for finding in requested_day.findings] == ["session-1"]
