from datetime import datetime, timedelta

from app.platform.scheduler.schedule_models import ScheduleFrequency


class ScheduleCalculator:
    def next_run_after(self, value: datetime, frequency: ScheduleFrequency) -> datetime:
        if frequency == ScheduleFrequency.HOURLY:
            return value + timedelta(hours=1)
        if frequency == ScheduleFrequency.DAILY:
            return value + timedelta(days=1)
        if frequency == ScheduleFrequency.WEEKLY:
            return value + timedelta(weeks=1)

        raise ValueError(f"Unsupported schedule frequency: {frequency}")
