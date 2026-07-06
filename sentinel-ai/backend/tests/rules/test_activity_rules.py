from datetime import datetime

from app.matcher.services.activity_matcher import ActivityMatcher
from app.rules.activity.extended_manual_activity_rule import ExtendedManualActivityRule
from app.rules.activity.inserted_manual_activity_rule import InsertedManualActivityRule
from app.rules.domain.rule_context import RuleContext
from app.timeline.domain.activity_snapshot import ActivitySnapshot
from app.timeline.domain.source import DataSource
from app.timeline.services.timeline_builder import TimelineBuilder


def dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


def activity(external_id: str, source: DataSource, start: str, end: str, duration: int) -> ActivitySnapshot:
    return ActivitySnapshot(
        external_id=external_id,
        login_session_external_id="LS-1",
        data_source=source,
        start_time=dt(start),
        end_time=dt(end),
        duration_seconds=duration,
        activity_type_id=1,
    )


def test_inserted_manual_activity_rule_returns_evidence() -> None:
    comparison = [activity("agent-1", DataSource.AGENT, "2026-07-01T09:00:00", "2026-07-01T09:30:00", 1800)]
    matches = ActivityMatcher().match_sources([], comparison, DataSource.SYSTEM, DataSource.AGENT)
    timeline = TimelineBuilder().build("LS-1", comparison)
    context = RuleContext("LS-1", timeline, {(DataSource.SYSTEM, DataSource.AGENT): matches})

    results = InsertedManualActivityRule(DataSource.SYSTEM, DataSource.AGENT).evaluate(context)

    assert len(results) == 1
    assert results[0].evidence[0].evidence_type == "inserted_activity"


def test_extended_manual_activity_rule_returns_evidence() -> None:
    baseline = [activity("sys-1", DataSource.SYSTEM, "2026-07-01T08:00:00", "2026-07-01T09:00:00", 3600)]
    comparison = [activity("agent-1", DataSource.AGENT, "2026-07-01T08:00:00", "2026-07-01T09:30:00", 5400)]
    matches = ActivityMatcher().match_sources(baseline, comparison, DataSource.SYSTEM, DataSource.AGENT)
    timeline = TimelineBuilder().build("LS-1", baseline + comparison)
    context = RuleContext("LS-1", timeline, {(DataSource.SYSTEM, DataSource.AGENT): matches})

    results = ExtendedManualActivityRule(DataSource.SYSTEM, DataSource.AGENT).evaluate(context)

    assert len(results) == 1
    assert results[0].evidence[0].payload["delta_seconds"] == 1800
