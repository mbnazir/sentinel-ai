from app.platform.events.event_bus import DomainEventBus
from app.platform.events.event_models import DomainEvent
from app.platform.events.event_repository import DomainEventRepository


class DomainEventDispatcher:
    """Persists event first, then dispatches to in-process subscribers."""

    def __init__(
        self,
        repository: DomainEventRepository,
        bus: DomainEventBus | None = None,
    ) -> None:
        self.repository = repository
        self.bus = bus or DomainEventBus()

    async def dispatch(self, event: DomainEvent) -> DomainEvent:
        saved = self.repository.save(event)
        await self.bus.publish(saved)
        return saved
