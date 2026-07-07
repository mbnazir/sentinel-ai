from app.platform.events.event_models import DomainEvent, EventType
from app.platform.jobs.job_models import JobRequest, JobType
from app.platform.jobs.job_service import JobService


class JobEnqueueingEventSubscriber:
    """Converts high-level events into follow-up jobs.

    This is intentionally conservative. It only emits the next obvious workflow step.
    """

    def __init__(self, job_service: JobService) -> None:
        self.job_service = job_service

    async def on_quartz_sync_completed(self, event: DomainEvent) -> None:
        result = event.payload.get("result") or {}
        shift_date_from = result.get("shift_date_from") or event.payload.get("shift_date_from")
        shift_date_to = result.get("shift_date_to") or event.payload.get("shift_date_to")

        if not shift_date_from or not shift_date_to:
            return

        self.job_service.enqueue(
            JobRequest(
                job_type=JobType.SCAN_RUN,
                organization_id=event.organization_id,
                payload={
                    "shift_date_from": shift_date_from,
                    "shift_date_to": shift_date_to,
                },
                requested_by="event-bus",
            )
        )

    async def on_scan_completed(self, event: DomainEvent) -> None:
        self.job_service.enqueue(
            JobRequest(
                job_type=JobType.BEHAVIOR_REFRESH,
                organization_id=event.organization_id,
                payload={"source_event_id": event.event_id},
                requested_by="event-bus",
            )
        )


def register_workflow_subscribers(bus, subscriber: JobEnqueueingEventSubscriber) -> None:
    bus.subscribe(EventType.QUARTZ_SYNC_COMPLETED, subscriber.on_quartz_sync_completed)
    bus.subscribe(EventType.SCAN_COMPLETED, subscriber.on_scan_completed)
