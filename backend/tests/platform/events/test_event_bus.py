from app.platform.events.event_bus import DomainEventBus
from app.platform.events.event_models import DomainEvent, EventType


async def test_event_bus_invokes_subscriber() -> None:
    bus = DomainEventBus()
    received = []

    async def handler(event):
        received.append(event.event_id)

    bus.subscribe(EventType.SCAN_COMPLETED, handler)
    event = DomainEvent.create(EventType.SCAN_COMPLETED, "ORG1")

    await bus.publish(event)

    assert received == [event.event_id]
