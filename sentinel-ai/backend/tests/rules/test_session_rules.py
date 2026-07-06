from datetime import datetime

from app.rules.domain.rule_context import RuleContext
from app.rules.session.manual_source_duration_increase_rule import ManualSourceDurationIncreaseRule
from app.timeline.domain.activity_snapshot import ActivitySnapshot
from app.timeline.domain.source import DataSource
from app.timeline.services.timeline_builder import TimelineBuilder


def dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


def test_manual_source_duration_increase_rule_flags_large_delta() -> None:
    activities = [
        ActivitySnapshot("sys-1", "LS-1", DataSource.SYSTEM, dt("2026-07-01T08:00:00"), dt("2026-07-01T09:00:00"), 3600, 1),
        ActivitySnapshot("pay-1", "LS-1", DataSource.PAYROLL, dt("2026-07-01T08:00:00"), dt("2026-07-01T10:00:00"), 7200, 1),
    ]
    timeline = TimelineBuilder().build("LS-1", activities)
    context = RuleContext("LS-1", timeline)

    results = ManualSourceDurationIncreaseRule(DataSource.SYSTEM, DataSource.PAYROLL, 1800).evaluate(context)

    assert len(results) == 1
    assert results[0].severity.value == "critical"
