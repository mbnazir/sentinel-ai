from app.investigations.domain.case import InvestigationCase
from app.platform.events.event_models import DomainEvent, EventType


class InvestigationEventFactory:
    def case_created(self, case: InvestigationCase, correlation_id: str | None = None) -> DomainEvent:
        return DomainEvent.create(
            event_type=EventType.CASE_CREATED,
            organization_id=case.organization_id,
            payload={
                "case_id": case.case_id,
                "entity_type": case.entity_type,
                "entity_id": case.entity_id,
                "risk_score": case.risk_score,
                "priority": case.priority.value,
                "status": case.status.value,
            },
            correlation_id=correlation_id,
            causation_id=case.case_id,
        )

    def case_updated(self, case: InvestigationCase, action: str, correlation_id: str | None = None) -> DomainEvent:
        return DomainEvent.create(
            event_type=EventType.CASE_UPDATED,
            organization_id=case.organization_id,
            payload={
                "case_id": case.case_id,
                "action": action,
                "entity_type": case.entity_type,
                "entity_id": case.entity_id,
                "risk_score": case.risk_score,
                "priority": case.priority.value,
                "status": case.status.value,
            },
            correlation_id=correlation_id,
            causation_id=case.case_id,
        )
