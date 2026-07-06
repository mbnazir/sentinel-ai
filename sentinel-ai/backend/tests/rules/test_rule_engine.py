from datetime import datetime

from app.matcher.services.activity_matcher import ActivityMatcher
from app.rules.engine.rule_engine import RuleEngine
from app.rules.activity.extended_manual_activity_rule import ExtendedManualActivityRule
from app.rules.domain.rule_context import RuleContext
from app.timeline.domain.activity_snapshot import ActivitySnapshot
from app.timeline.domain.source import DataSource
from app.timeline.services.timeline_builder import TimelineBuilder


def dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


def test_rule_engine_executes_registered_rules() -> None:
    baseline = [
        ActivitySnapshot("sys-1", "LS-1", DataSource.SYSTEM, dt("2026-07-01T08:00:00"), dt("2026-07-01T09:00:00"), 3600, 1)
    ]
    comparison = [
        ActivitySnapshot("sup-1", "LS-1", DataSource.SUPERVISOR, dt("2026-07-01T08:00:00"), dt("2026-07-01T09:45:00"), 6300, 1)
    ]
    timeline = TimelineBuilder().build("LS-1", baseline + comparison)
    matches = ActivityMatcher().match_sources(baseline, comparison, DataSource.SYSTEM, DataSource.SUPERVISOR)
    context = RuleContext("LS-1", timeline, {(DataSource.SYSTEM, DataSource.SUPERVISOR): matches})
    engine = RuleEngine([ExtendedManualActivityRule(DataSource.SYSTEM, DataSource.SUPERVISOR)])

    results = engine.evaluate(context)

    assert len(results) == 1
    assert results[0].rule_id == "ACT_EXTENDED_SYSTEM_SUPERVISOR"
