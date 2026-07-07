from collections import defaultdict
from collections.abc import Awaitable, Callable

from app.platform.events.event_models import DomainEvent, EventType

EventHandler = Callable[[DomainEvent], Awaitable[None]]


class DomainEventBus:
    def __init__(self) -> None:
        self._handlers: dict[EventType, list[EventHandler]] = defaultdict(list)

    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        self._handlers[event_type].append(handler)

    async def publish(self, event: DomainEvent) -> None:
        for handler in self._handlers.get(event.event_type, []):
            await handler(event)
