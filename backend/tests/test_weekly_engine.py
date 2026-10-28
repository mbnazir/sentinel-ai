from datetime import date, datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.weekly.builder import week_bounds
from app.weekly.attribution import attribute_adjustments
from app.weekly.models import (ActorStatus, PayrollWeek, ResolutionStatus,
                               WeeklyAdjustment, WeeklyEvidenceQuality,
                               WeeklyImpactAssessment, WeeklySession)
from app.weekly.overtime import calculate_overtime
from app.weekly.payable import resolve_session_payable
from app.weekly.rules import evaluate_weekly_rules, repeated_actor_employee_patterns
from app.weekly.builder import load_payroll_week


def test_sunday_saturday_week_boundaries():
    assert week_bounds(date(2026, 8, 26)) == (date(2026, 8, 23), date(2026, 8, 29))
    assert week_bounds(date(2026, 8, 23)) == (date(2026, 8, 23), date(2026, 8, 29))


@pytest.mark.parametrize(("baseline", "final", "expected"), [
    (144000, 144000, 0), (144000, 172800, 28800), (158400, 172800, 14400),
])
def test_overtime_math(baseline, final, expected):
    summary = calculate_overtime(employee_id="e", week_start=date(2026, 8, 23), week_end=date(2026, 8, 29),
        baseline_eligible_seconds=Decimal(baseline), final_eligible_seconds=Decimal(final))
    assert summary.incremental_overtime_seconds == Decimal(expected)


def test_fractional_metadata_is_preserved_provisionally():
    payable = resolve_session_payable({"regular_hour": "28800.125", "overtime": 0.5})
    assert payable.total_seconds == Decimal("28800.625")
    assert payable.status == ResolutionStatus.PROVISIONAL


@pytest.mark.parametrize("metadata", [{}, {"regular_hour": -1}, {"regular_hour": "NaN"},
                                      {"regular_hour": "bad", "overtime": 0}])
def test_missing_or_invalid_metadata_is_not_payable(metadata):
    assert resolve_session_payable(metadata).status == ResolutionStatus.INSUFFICIENT_DATA


def test_missing_calculation_inputs_never_manufacture_baseline():
    result = calculate_overtime(employee_id="e", week_start=date(2026, 8, 23), week_end=date(2026, 8, 29),
                                baseline_eligible_seconds=None, final_eligible_seconds=Decimal(172800))
    assert result.baseline_overtime_seconds is None
    assert result.status == ResolutionStatus.INSUFFICIENT_DATA


def _session(day=date(2026, 8, 25), sid="s", run=None, **kwargs):
    return WeeklySession(source_session_id=sid, employee_id="e", shift_date=day,
        start_at=datetime(2026, 8, 25, 9, tzinfo=timezone.utc),
        end_at=datetime(2026, 8, 25, 17, tzinfo=timezone.utc), ingestion_run_id=run or uuid4(), **kwargs)


def _assessment(*, quality=WeeklyEvidenceQuality.COMPLETE, status=ResolutionStatus.VERIFIED,
                total=Decimal(172800), adjustments=(), provenance=None):
    run = uuid4()
    week = PayrollWeek(employee_id="e", start_date=date(2026, 8, 23), end_date=date(2026, 8, 29),
        ingestion_run_id=run, completeness=quality)
    summary = calculate_overtime(employee_id="e", week_start=week.start_date, week_end=week.end_date,
        baseline_eligible_seconds=Decimal(144000), final_eligible_seconds=total,
        adjustments=adjustments, status=status)
    return WeeklyImpactAssessment(payroll_week=week, sessions=(), adjustments=tuple(adjustments),
        summary=summary, provenance=provenance or {})


def test_wf001_positive_adjustment_is_lead_not_verdict():
    adj = WeeklyAdjustment(adjustment_id="a", employee_id="e", source_session_id="s",
        shift_date=date(2026, 8, 25), delta_seconds=Decimal(28800))
    findings = evaluate_weekly_rules(_assessment(quality=WeeklyEvidenceQuality.UNVERIFIED,
                                                  status=ResolutionStatus.PROVISIONAL,
                                                  adjustments=(adj,)))
    assert any(x.get("rule_id") == "WF-001" and x["classification"] == "investigative_lead" for x in findings)
    assert not any(x.get("rule_id") == "WF-002" for x in findings)


def test_wf002_verified_complete_incremental_overtime():
    findings = evaluate_weekly_rules(_assessment())
    assert any(x.get("rule_id") == "WF-002" and x["incremental_overtime_seconds"] == "28800" for x in findings)


def test_wf003_cross_day_requires_overtime_reached_date_evidence():
    adj = WeeklyAdjustment(adjustment_id="tue-edit", employee_id="e", source_session_id="s",
        shift_date=date(2026, 8, 25), delta_seconds=Decimal(28800))
    assessment = _assessment(adjustments=(adj,), provenance={"overtime_reached_on": "2026-08-27"})
    assert any(x.get("rule_id") == "WF-003" for x in evaluate_weekly_rules(assessment))
    assert not any(x.get("rule_id") == "WF-003" for x in evaluate_weekly_rules(_assessment(adjustments=(adj,))))


def test_wf004_requires_repeated_verified_actor_and_complete_weeks():
    actor_adj = WeeklyAdjustment(adjustment_id="x", employee_id="e", source_session_id="s",
        shift_date=date(2026, 8, 25), delta_seconds=Decimal(1), actor_id="u1",
        actor_status=ActorStatus.VERIFIED)
    first = _assessment(adjustments=(actor_adj,))
    second = first.model_copy(update={"payroll_week": first.payroll_week.model_copy(
        update={"start_date": date(2026, 8, 30), "end_date": date(2026, 9, 5)})})
    assert repeated_actor_employee_patterns((first, second)) == ()
    results = repeated_actor_employee_patterns((first, second), comparison_population_reliable=True)
    assert len(results) == 1 and results[0]["rule_id"] == "WF-004"
    provisional = first.model_copy(update={"payroll_week": first.payroll_week.model_copy(
        update={"completeness": WeeklyEvidenceQuality.UNVERIFIED})})
    assert repeated_actor_employee_patterns((provisional, second),
                                            comparison_population_reliable=True) == ()


def test_attribution_never_uses_assigned_supervisor_as_editor():
    session = _session(supervisor_id="supervisor-9")
    raw = SimpleNamespace(source_session_id="s", source_activity_id="activity-1", data_source_id=3,
        metadata={"before_seconds": 28800, "after_seconds": 57600}, updated_at=None, created_at=None)
    adjustment, = attribute_adjustments(employee_id="e", sessions=(session,), activities=(raw,))
    assert adjustment.actor_id == "ACTOR_UNVERIFIED"
    assert adjustment.actor_status == ActorStatus.ACTOR_UNVERIFIED


def test_attribution_only_verifies_explicitly_verified_identity_and_flags_conflict():
    session = _session()
    good = SimpleNamespace(source_session_id="s", source_activity_id="a", data_source_id=4,
        metadata={"before_seconds": "1.1", "after_seconds": "2.2", "editor_id": "m1", "actor_verified": True},
        updated_at=None, created_at=None)
    bad = SimpleNamespace(source_session_id="s", source_activity_id="b", data_source_id=5,
        metadata={"before_seconds": 1, "after_seconds": 2, "editor_id": "m1", "actor_id": "m2"},
        updated_at=None, created_at=None)
    good_adj, bad_adj = attribute_adjustments(employee_id="e", sessions=(session,), activities=(good, bad))
    assert good_adj.actor_status == ActorStatus.VERIFIED and good_adj.delta_seconds == Decimal("1.1")
    assert bad_adj.actor_status == ActorStatus.CONFLICTING


def test_multiple_adjustments_are_deduplicated_by_source_activity_id():
    session = _session()
    raw = SimpleNamespace(source_session_id="s", source_activity_id="a", data_source_id=3,
        metadata={"before_seconds": 0, "after_seconds": 60}, updated_at=None, created_at=None)
    result = attribute_adjustments(employee_id="e", sessions=(session,), activities=(raw, raw))
    assert len(result) == 1


def test_overtime_math_is_idempotent_and_preserves_fractional_seconds():
    args = dict(employee_id="e", week_start=date(2026, 8, 23), week_end=date(2026, 8, 29),
        baseline_eligible_seconds=Decimal("144000.125"), final_eligible_seconds=Decimal("144001.375"))
    first, second = calculate_overtime(**args), calculate_overtime(**args)
    assert first.model_dump() == second.model_dump()
    assert first.incremental_overtime_seconds == Decimal("1.250")


@pytest.mark.asyncio
@pytest.mark.parametrize(("status", "quality"), [
    ("failed", WeeklyEvidenceQuality.INCOMPLETE),
    ("running", WeeklyEvidenceQuality.INCOMPLETE),
    ("queued", WeeklyEvidenceQuality.INCOMPLETE),
    ("completed", WeeklyEvidenceQuality.UNVERIFIED),
])
async def test_week_builder_distinguishes_failed_partial_and_unreconciled_runs(status, quality):
    run_id = uuid4()
    run = SimpleNamespace(status=status, shift_date_from=date(2026, 8, 23), shift_date_to=date(2026, 8, 29),
        session_count=1)
    row = SimpleNamespace(source_session_id="s", agent_id="e", shift_date=date(2026, 8, 25),
        start_at=datetime(2026, 8, 25, 9, tzinfo=timezone.utc), end_at=datetime(2026, 8, 25, 17, tzinfo=timezone.utc),
        ingestion_run_id=run_id, supervisor_id="sup", manager_id="mgr", metadata_json={})
    db = AsyncMock()
    db.get.return_value = run
    db.execute = AsyncMock(return_value=SimpleNamespace(scalars=lambda: iter([row])))
    week, sessions = await load_payroll_week(db, ingestion_run_id=run_id, employee_id="e", day=date(2026, 8, 26))
    assert week.completeness == quality
    assert week.source_count_reconciled is False
    assert len(week.missing_dates) == 6
    assert sessions[0].ingestion_run_id == run_id


@pytest.mark.asyncio
async def test_week_builder_never_mixes_other_ingestion_runs():
    run_id, other_run = uuid4(), uuid4()
    run = SimpleNamespace(status="completed", shift_date_from=date(2026, 8, 23),
        shift_date_to=date(2026, 8, 29), session_count=1)
    row = SimpleNamespace(source_session_id="s", agent_id="e", shift_date=date(2026, 8, 25),
        start_at=datetime(2026, 8, 25, 9, tzinfo=timezone.utc), end_at=None,
        ingestion_run_id=run_id, supervisor_id=None, manager_id=None, metadata_json={})
    db = AsyncMock()
    db.get.return_value = run
    db.execute = AsyncMock(return_value=SimpleNamespace(scalars=lambda: iter([row])))
    _, sessions = await load_payroll_week(db, ingestion_run_id=run_id, employee_id="e", day=date(2026, 8, 25))
    assert sessions[0].ingestion_run_id != other_run


@pytest.mark.asyncio
async def test_overlapping_sessions_are_reported_without_summing_intervals():
    run_id = uuid4()
    run = SimpleNamespace(status="completed", shift_date_from=date(2026, 8, 23),
        shift_date_to=date(2026, 8, 29), session_count=2)
    base = dict(agent_id="e", shift_date=date(2026, 8, 25), end_at=datetime(2026, 8, 25, 12,
        tzinfo=timezone.utc), ingestion_run_id=run_id, supervisor_id=None, manager_id=None, metadata_json={})
    rows = [SimpleNamespace(source_session_id="a", start_at=datetime(2026, 8, 25, 9, tzinfo=timezone.utc), **base),
            SimpleNamespace(source_session_id="b", start_at=datetime(2026, 8, 25, 11, tzinfo=timezone.utc), **base)]
    db = AsyncMock()
    db.get.return_value = run
    db.execute = AsyncMock(return_value=SimpleNamespace(scalars=lambda: iter(rows)))
    week, _ = await load_payroll_week(db, ingestion_run_id=run_id, employee_id="e", day=date(2026, 8, 25))
    assert week.provenance["overlapping_session_pairs"] == [{
        "session_a": "a", "session_b": "b", "start_at": "2026-08-25T11:00:00+00:00",
        "end_at": "2026-08-25T12:00:00+00:00"}]
