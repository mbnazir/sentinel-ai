from app.platform.events.event_bus import DomainEventBus
from app.platform.events.event_models import DomainEvent, EventType
from app.platform.events.integration.event_subscribers import (
    JobEnqueueingEventSubscriber,
    register_workflow_subscribers,
)


class MemoryJobService:
    def __init__(self):
        self.requests = []

    def enqueue(self, request):
        self.requests.append(request)
        return request


async def test_scan_completed_enqueues_behavior_refresh() -> None:
    bus = DomainEventBus()
    jobs = MemoryJobService()
    register_workflow_subscribers(bus, JobEnqueueingEventSubscriber(jobs))

    await bus.publish(DomainEvent.create(EventType.SCAN_COMPLETED, "ORG1"))

    assert len(jobs.requests) == 1
    assert jobs.requests[0].job_type.value == "behavior_refresh"
