from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from app.weekly.activity_comparison import compare_activity_versions
from app.weekly.activity_models import (ActivityChangeType, ActivityInterval,
                                        ActivityVersion, ComparisonStatus)

RUN = uuid4()
SESSION = "180596739"
SYSTEM = "quartz"


def dt(hour: int, minute: int = 0, second: int = 0, microsecond: int = 0):
    return datetime(2026, 8, 25, hour, minute, second, microsecond, tzinfo=UTC)


def interval(activity_id, source, activity_type, start, end, *, duration=None, comment=None,
             created=None, updated=None, run=RUN, session=SESSION, system=SYSTEM):
    return ActivityInterval(activity_id=str(activity_id), data_source_id=source,
        activity_type_id=activity_type, start_at=start, end_at=end,
        duration_seconds=Decimal(duration) if duration is not None else None, comment=comment,
        source_created_at=created, source_updated_at=updated, source_system=system,
        source_session_id=session, ingestion_run_id=run)


def version(source_id, *rows, run=RUN, session=SESSION, system=SYSTEM):
    return ActivityVersion(ingestion_run_id=run, source_system=system,
        source_session_id=session, data_source_id=source_id,
        version_id=f"quartz-source-{source_id}", activities=tuple(rows))


def compare(old, new, *, run=RUN, session=SESSION):
    return compare_activity_versions(old, new, ingestion_run_id=run, source_system=SYSTEM,
        source_session_id=session, original_source_id=2, revised_source_id=3)


def test_exact_regression_163_second_activity_reclassification():
    agent_created = datetime(2026, 8, 26, 13, 27, 55, tzinfo=UTC)
    supervisor_created = datetime(2026, 8, 26, 16, 38, 13, tzinfo=UTC)
    old = version(2, interval("agent-a", 2, 2, dt(11, 55), dt(12), duration=300,
                               comment="bio", created=agent_created))
    new = version(3,
        interval("sup-a", 3, 2, dt(11, 55), dt(11, 57, 17), duration=137,
                 comment="edited", created=supervisor_created),
        interval("sup-b", 3, 7, dt(11, 57, 17), dt(12), duration=163,
                 comment="OT Break", created=supervisor_created),
    )
    result = compare(old, new)
    changed = [c for c in result.changes if c.change_type == ActivityChangeType.RECLASSIFIED]
    assert len(changed) == 1
    assert changed[0].affected_seconds == Decimal(163)
    assert changed[0].net_covered_seconds == Decimal(0)
    assert changed[0].original_activity_type_ids == (2,)
    assert changed[0].revised_activity_type_ids == (7,)
    assert result.net_covered_seconds == Decimal(0)
    assert result.reclassified_seconds == Decimal(163)
    assert result.finding["code"] == "WF-005"
    assert result.finding["editor_identity"] == "UNVERIFIED"
    assert result.finding["financial_impact"] == "UNVERIFIED"
    assert result.readiness.status == ComparisonStatus.READY


def test_different_activity_ids_with_same_classification_are_unchanged():
    result = compare(version(2, interval("old-id", 2, 4, dt(10), dt(10, 0, 5))),
                     version(3, interval("new-id", 3, 4, dt(10), dt(10, 0, 5))))
    assert [x.change_type for x in result.changes] == [ActivityChangeType.UNCHANGED]
    assert result.finding is None
    assert result.net_covered_seconds == 0


def test_added_and_removed_nonadjacent_time_are_reported_without_inflation_claim():
    old = version(2, interval("old", 2, 1, dt(10), dt(10, 0, 5)))
    new = version(3, interval("kept", 3, 1, dt(10), dt(10, 0, 5)),
                  interval("extra", 3, 8, dt(10, 0, 10), dt(10, 0, 15)))
    added = compare(old, new)
    assert any(c.change_type == ActivityChangeType.ADDED and c.affected_seconds == 5 for c in added.changes)
    assert added.net_covered_seconds == 5
    removed = compare(version(2, interval("old", 2, 1, dt(10), dt(10, 0, 5)),
                                interval("gone", 2, 8, dt(10, 0, 10), dt(10, 0, 15))),
                      version(3, interval("kept", 3, 1, dt(10), dt(10, 0, 5))))
    assert any(c.change_type == ActivityChangeType.REMOVED and c.affected_seconds == 5
               for c in removed.changes)
    assert removed.net_covered_seconds == -5


@pytest.mark.parametrize(("old_end", "new_end", "expected", "net"), [
    (10, 15, ActivityChangeType.EXTENDED, Decimal(5)),
    (15, 10, ActivityChangeType.SHORTENED, Decimal(-5)),
])
def test_boundary_extension_and_shortening(old_end, new_end, expected, net):
    old = version(2, interval("o", 2, 1, dt(10), dt(10, 0, old_end)))
    new = version(3, interval("n", 3, 1, dt(10), dt(10, 0, new_end)))
    result = compare(old, new)
    changed = [c for c in result.changes if c.change_type == expected]
    assert sum(c.affected_seconds for c in changed) == 5
    assert sum(c.net_covered_seconds for c in changed) == net


def test_activity_split_and_merge_do_not_create_change_or_double_count():
    whole = version(2, interval("whole", 2, 5, dt(10), dt(10, 0, 20)))
    split = version(3, interval("a", 3, 5, dt(10), dt(10, 0, 10)),
                    interval("b", 3, 5, dt(10, 0, 10), dt(10, 0, 20)))
    split_result = compare(whole, split)
    assert all(c.change_type == ActivityChangeType.UNCHANGED for c in split_result.changes)
    assert sum(c.affected_seconds for c in split_result.changes) == Decimal(20)
    merged = compare(split, version(3, interval("merged", 3, 5, dt(10), dt(10, 0, 20))))
    assert all(c.change_type == ActivityChangeType.UNCHANGED for c in merged.changes)
    assert sum(c.affected_seconds for c in merged.changes) == Decimal(20)


def test_conflicting_overlapping_types_are_ambiguous_and_not_double_counted():
    old = version(2, interval("a", 2, 1, dt(10), dt(10, 0, 10)),
                  interval("b", 2, 2, dt(10, 0, 5), dt(10, 0, 15)))
    new = version(3, interval("c", 3, 1, dt(10), dt(10, 0, 15)))
    result = compare(old, new)
    assert result.readiness.conflicting_segments > 0
    assert any(c.change_type == ActivityChangeType.AMBIGUOUS for c in result.changes)
    assert result.net_covered_seconds == Decimal(0)
    assert sum((c.affected_seconds or 0) for c in result.changes) == Decimal(15)


def test_missing_source_version_is_incomplete_and_financial_impact_unverified():
    result = compare(version(2, interval("a", 2, 1, dt(10), dt(10, 0, 5))), None)
    assert result.readiness.status == ComparisonStatus.INCOMPLETE
    assert result.readiness.missing_source_ids == (3,)
    assert result.finding is None
    assert result.net_covered_seconds is None


def test_missing_end_and_negative_interval_are_ambiguous():
    open_row = interval("open", 2, 1, dt(10), None)
    negative = interval("negative", 3, 1, dt(10, 0, 10), dt(10))
    result = compare(version(2, open_row), version(3, negative))
    assert result.readiness.status == ComparisonStatus.INCOMPLETE
    assert set(result.readiness.malformed_activity_ids) == {"open", "negative"}
    assert all(c.change_type == ActivityChangeType.AMBIGUOUS for c in result.changes)
    assert result.net_covered_seconds is None


def test_fractional_boundaries_are_exact_and_duration_mismatch_is_flagged():
    start, end = dt(10, microsecond=125000), dt(10, 0, 1, 625000)
    result = compare(version(2, interval("a", 2, 1, start, end, duration=1)),
                     version(3, interval("b", 3, 1, start, end, duration=Decimal("1.5"))))
    assert result.changes[0].affected_seconds == Decimal("1.5")
    assert result.readiness.duration_mismatch_activity_ids == ()
    inconsistent = compare(version(2, interval("a", 2, 1, start, end, duration=4)),
                           version(3, interval("b", 3, 1, start, end, duration=Decimal("1.5"))))
    assert inconsistent.readiness.status == ComparisonStatus.PROVISIONAL
    assert inconsistent.readiness.duration_mismatch_activity_ids == ("a",)


def test_comparison_refuses_to_mix_runs_with_same_session_id():
    other_run = uuid4()
    old = version(2, interval("a", 2, 1, dt(10), dt(10, 0, 5), run=RUN))
    new = version(3, interval("b", 3, 2, dt(10), dt(10, 0, 5), run=other_run), run=other_run)
    result = compare(old, new)
    assert result.readiness.status == ComparisonStatus.INCOMPLETE
    assert result.changes == ()
    assert result.net_covered_seconds is None


def test_no_timestamps_claim_editor_or_payable_impact():
    old = version(2, interval("a", 2, 1, dt(10), dt(10, 0, 5), created=dt(10)))
    new = version(3, interval("b", 3, 2, dt(10), dt(10, 0, 5), created=dt(11)))
    result = compare(old, new)
    signal = result.finding
    assert signal["editor_identity"] == "UNVERIFIED"
    assert signal["financial_impact"] == "UNVERIFIED"
    assert result.changes[0].evidence.original_created_at == (dt(10),)
    assert result.changes[0].evidence.revised_created_at == (dt(11),)


def test_activity_versions_reject_cross_source_record_keys():
    old = version(2, interval("a", 2, 1, dt(10), dt(10, 0, 5)))
    wrong_session = version(3, interval("b", 3, 2, dt(10), dt(10, 0, 5), session="other"))
    result = compare(old, wrong_session)
    assert result.readiness.status == ComparisonStatus.INCOMPLETE
    assert result.changes == ()


def test_unsupported_source_ids_are_incomplete_and_suppress_wf005():
    old = version(9, interval("a", 9, 1, dt(10), dt(10, 0, 5)))
    new = version(3, interval("b", 3, 2, dt(10), dt(10, 0, 5)))
    result = compare(old, new)
    assert result.readiness.status == ComparisonStatus.INCOMPLETE
    assert result.changes == ()
    assert result.finding is None
