from app.platform.events.event_bus import DomainEventBus
from app.platform.events.event_models import DomainEvent, EventType


async def log_event_subscriber(event: DomainEvent) -> None:
    # Placeholder subscriber. Later milestones will enqueue jobs here.
    return None


def build_default_event_bus() -> DomainEventBus:
    bus = DomainEventBus()
    for event_type in EventType:
        bus.subscribe(event_type, log_event_subscriber)
    return bus
