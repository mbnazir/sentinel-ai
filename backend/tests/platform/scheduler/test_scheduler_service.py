from datetime import datetime, timezone

from app.platform.jobs.job_models import JobType
from app.platform.scheduler.schedule_models import JobSchedule, ScheduleFrequency, ScheduleStatus
from app.platform.scheduler.scheduler_service import SchedulerService


class MemoryScheduleRepository:
    def __init__(self):
        self.items = []

    def save(self, schedule):
        existing = [item for item in self.items if item.schedule_id == schedule.schedule_id]
        if existing:
            self.items[self.items.index(existing[0])] = schedule
        else:
            self.items.append(schedule)
        return schedule

    def list_due(self, now, limit=100):
        return [item for item in self.items if item.status == ScheduleStatus.ACTIVE and item.next_run_at <= now]


class MemoryJobService:
    def __init__(self):
        self.jobs = []

    def enqueue(self, request):
        job = type("Job", (), {"job_id": f"JOB-{len(self.jobs)+1}"})()
        self.jobs.append((job, request))
        return job


def test_run_due_enqueues_job_and_updates_schedule() -> None:
    now = datetime(2026, 7, 1, 8, tzinfo=timezone.utc)
    repo = MemoryScheduleRepository()
    job_service = MemoryJobService()
    service = SchedulerService(repo, job_service)

    repo.save(
        JobSchedule(
            schedule_id="SCH1",
            name="Daily scan",
            organization_id="ORG1",
            job_type=JobType.SCAN_RUN,
            frequency=ScheduleFrequency.DAILY,
            payload={},
            status=ScheduleStatus.ACTIVE,
            next_run_at=now,
        )
    )

    job_ids = service.run_due(now)

    assert job_ids == ["JOB-1"]
    assert repo.items[0].last_run_at == now
    assert repo.items[0].next_run_at > now
