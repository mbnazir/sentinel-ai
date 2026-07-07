from sqlalchemy.orm import Session

from app.infrastructure.persistence.models_events import DomainEventModel
from app.platform.events.event_models import DomainEvent, EventType


class DomainEventRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, event: DomainEvent) -> DomainEvent:
        self.session.add(
            DomainEventModel(
                event_id=event.event_id,
                event_type=event.event_type.value,
                organization_id=event.organization_id,
                payload=event.payload,
                correlation_id=event.correlation_id,
                causation_id=event.causation_id,
                occurred_at=event.occurred_at,
            )
        )
        self.session.commit()
        return event

    def list(
        self,
        organization_id: str | None = None,
        event_type: EventType | None = None,
        limit: int = 100,
    ) -> list[DomainEvent]:
        query = self.session.query(DomainEventModel)

        if organization_id:
            query = query.filter_by(organization_id=organization_id)
        if event_type:
            query = query.filter_by(event_type=event_type.value)

        rows = query.order_by(DomainEventModel.occurred_at.desc()).limit(limit).all()
        return [self._to_domain(row) for row in rows]

    def _to_domain(self, row: DomainEventModel) -> DomainEvent:
        return DomainEvent(
            event_id=row.event_id,
            event_type=EventType(row.event_type),
            organization_id=row.organization_id,
            payload=row.payload or {},
            correlation_id=row.correlation_id,
            causation_id=row.causation_id,
            occurred_at=row.occurred_at,
        )
