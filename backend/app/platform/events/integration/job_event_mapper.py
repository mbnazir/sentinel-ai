from app.platform.events.event_models import DomainEvent, EventType
from app.platform.jobs.job_models import JobRecord, JobStatus, JobType


class JobEventMapper:
    """Maps job lifecycle outcomes into domain events."""

    def to_completion_event(self, job: JobRecord) -> DomainEvent | None:
        if job.status != JobStatus.SUCCEEDED:
            return None

        event_type = {
            JobType.QUARTZ_SYNC: EventType.QUARTZ_SYNC_COMPLETED,
            JobType.SCAN_RUN: EventType.SCAN_COMPLETED,
            JobType.BEHAVIOR_REFRESH: EventType.BEHAVIOR_PROFILE_REFRESHED,
            JobType.ANOMALY_SCORE: EventType.ANOMALY_DETECTED,
            JobType.ANOMALY_CASE_ATTACHMENT: EventType.CASE_UPDATED,
        }.get(job.job_type)

        if event_type is None:
            return None

        return DomainEvent.create(
            event_type=event_type,
            organization_id=job.organization_id,
            payload={
                "job_id": job.job_id,
                "job_type": job.job_type.value,
                "result": job.payload.get("_result"),
            },
            correlation_id=job.job_id,
            causation_id=job.job_id,
        )

    def to_failure_event(self, job: JobRecord) -> DomainEvent | None:
        if job.status != JobStatus.FAILED:
            return None

        return DomainEvent.create(
            event_type=EventType.JOB_FAILED,
            organization_id=job.organization_id,
            payload={
                "job_id": job.job_id,
                "job_type": job.job_type.value,
                "error_message": job.error_message,
                "attempt_count": job.payload.get("_attempt_count"),
            },
            correlation_id=job.job_id,
            causation_id=job.job_id,
        )
