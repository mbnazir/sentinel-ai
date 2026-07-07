from app.anomaly.cases.anomaly_case_attachment_service import AnomalyCaseAttachmentService
from app.anomaly.domain.anomaly_models import AnomalyScore
from app.infrastructure.persistence.repositories.investigation_repository import InvestigationRepository
from app.investigations.domain.case import InvestigationCase
from app.platform.events.event_dispatcher import DomainEventDispatcher
from app.platform.events.integration.investigation_event_factory import InvestigationEventFactory


class EventEmittingAnomalyCaseAttachmentService:
    """Wraps anomaly case attachment and emits case events."""

    def __init__(
        self,
        repository: InvestigationRepository,
        dispatcher: DomainEventDispatcher,
        factory: InvestigationEventFactory | None = None,
    ) -> None:
        self.repository = repository
        self.service = AnomalyCaseAttachmentService(repository)
        self.dispatcher = dispatcher
        self.factory = factory or InvestigationEventFactory()

    async def attach_or_create_case(
        self,
        organization_id: str,
        anomaly_score: AnomalyScore,
        minimum_score: int = 61,
        correlation_id: str | None = None,
    ) -> InvestigationCase | None:
        existing = self.service._find_open_case(
            organization_id,
            anomaly_score.entity_type,
            anomaly_score.entity_id,
        )
        case = self.service.attach_or_create_case(organization_id, anomaly_score, minimum_score)

        if case is None:
            return None

        event = (
            self.factory.case_updated(case, "anomaly_evidence_attached", correlation_id)
            if existing is not None
            else self.factory.case_created(case, correlation_id)
        )
        await self.dispatcher.dispatch(event)
        return case
