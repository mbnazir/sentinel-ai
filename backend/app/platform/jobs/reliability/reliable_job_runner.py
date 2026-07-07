from datetime import datetime, timezone
from dataclasses import replace

from app.platform.jobs.job_models import JobRecord, JobStatus
from app.platform.jobs.job_registry import JobHandlerRegistry
from app.platform.jobs.reliability.dead_letter import DeadLetterJob, InMemoryDeadLetterRepository
from app.platform.jobs.reliability.retry_policy import RetryPolicy


class ReliableJobRunner:
    """Executes one job with retry/dead-letter semantics.

    This runner is deliberately storage-agnostic. The repository only needs save/get behavior.
    """

    def __init__(
        self,
        repository,
        registry: JobHandlerRegistry,
        retry_policy: RetryPolicy | None = None,
        dead_letter_repository: InMemoryDeadLetterRepository | None = None,
    ) -> None:
        self.repository = repository
        self.registry = registry
        self.retry_policy = retry_policy or RetryPolicy()
        self.dead_letter_repository = dead_letter_repository or InMemoryDeadLetterRepository()

    async def run(self, job: JobRecord) -> JobRecord:
        attempt_count = int(job.payload.get("_attempt_count", 0)) + 1
        running = replace(
            job,
            status=JobStatus.RUNNING,
            started_at=datetime.now(timezone.utc),
            payload={**job.payload, "_attempt_count": attempt_count},
        )
        self.repository.save(running)

        try:
            result = await self.registry.get(running.job_type).handle(running)
            succeeded = replace(
                running,
                status=JobStatus.SUCCEEDED,
                finished_at=datetime.now(timezone.utc),
                payload={**running.payload, "_result": result},
                error_message=None,
            )
            return self.repository.save(succeeded)
        except Exception as exc:
            decision = self.retry_policy.evaluate(attempt_count)
            failed_payload = {
                **running.payload,
                "_last_error": str(exc),
                "_retry_decision": decision.reason,
                "_retry_delay_seconds": decision.delay_seconds,
            }

            if decision.should_retry:
                retry_job = replace(
                    running,
                    status=JobStatus.QUEUED,
                    finished_at=datetime.now(timezone.utc),
                    payload=failed_payload,
                    error_message=str(exc),
                )
                return self.repository.save(retry_job)

            dead = replace(
                running,
                status=JobStatus.FAILED,
                finished_at=datetime.now(timezone.utc),
                payload=failed_payload,
                error_message=str(exc),
            )
            saved = self.repository.save(dead)
            self.dead_letter_repository.add(
                DeadLetterJob(
                    job_id=saved.job_id,
                    job_type=saved.job_type.value,
                    organization_id=saved.organization_id,
                    payload=saved.payload,
                    error_message=str(exc),
                    failed_at=saved.finished_at,
                    attempt_count=attempt_count,
                )
            )
            return saved
