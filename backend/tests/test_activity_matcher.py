from datetime import UTC, datetime, timedelta

from app.domain.data_sources import ActivityDataSource
from app.matcher.activity_matcher import compare_activity_versions
from app.matcher.models import ActivityChangeType
from app.timeline.models import TimelineActivity

BASE = datetime(2026, 8, 26, 8, 0, tzinfo=UTC)


def activity(
    activity_id: str,
    source: ActivityDataSource,
    start_minute: int,
    end_minute: int,
    activity_type_id: int = 1,
) -> TimelineActivity:
    start = BASE + timedelta(minutes=start_minute)
    end = BASE + timedelta(minutes=end_minute)
    return TimelineActivity(
        source_activity_id=activity_id,
        source_session_id="1001",
        agent_id="42",
        data_source_id=source,
        activity_type_id=activity_type_id,
        start_at=start,
        end_at=end,
        duration_seconds=int((end - start).total_seconds()),
    )


def test_detects_extended_activity() -> None:
    result = compare_activity_versions(
        source_session_id="1001",
        baseline_source=ActivityDataSource.SYSTEM,
        comparison_source=ActivityDataSource.AGENT,
        baseline=[activity("s1", ActivityDataSource.SYSTEM, 0, 60)],
        comparison=[activity("a1", ActivityDataSource.AGENT, 0, 90)],
    )
    assert len(result.matches) == 1
    assert result.matches[0].change_type == ActivityChangeType.EXTENDED
    assert result.matches[0].duration_delta_seconds == 1800


def test_detects_removed_and_inserted_activities() -> None:
    result = compare_activity_versions(
        source_session_id="1001",
        baseline_source=ActivityDataSource.SYSTEM,
        comparison_source=ActivityDataSource.AGENT,
        baseline=[activity("s1", ActivityDataSource.SYSTEM, 0, 30)],
        comparison=[activity("a1", ActivityDataSource.AGENT, 90, 120)],
    )
    assert {match.change_type for match in result.matches} == {
        ActivityChangeType.REMOVED,
        ActivityChangeType.INSERTED,
    }


def test_detects_activity_type_change() -> None:
    result = compare_activity_versions(
        source_session_id="1001",
        baseline_source=ActivityDataSource.SYSTEM,
        comparison_source=ActivityDataSource.AGENT,
        baseline=[activity("s1", ActivityDataSource.SYSTEM, 0, 60, 7)],
        comparison=[activity("a1", ActivityDataSource.AGENT, 0, 60, 9)],
    )
    assert result.matches[0].change_type == ActivityChangeType.TYPE_CHANGED
    assert result.matches[0].activity_type_changed is True
