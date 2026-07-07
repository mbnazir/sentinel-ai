from datetime import datetime, timezone

from app.platform.scheduler.schedule_calculator import ScheduleCalculator
from app.platform.scheduler.schedule_models import ScheduleFrequency


def test_next_run_after_daily() -> None:
    now = datetime(2026, 7, 1, 8, tzinfo=timezone.utc)

    next_run = ScheduleCalculator().next_run_after(now, ScheduleFrequency.DAILY)

    assert next_run.day == 2
