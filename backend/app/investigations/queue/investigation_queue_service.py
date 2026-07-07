from datetime import datetime, timezone

from app.investigations.domain.case import InvestigationCase
from app.investigations.domain.priority import InvestigationPriority
from app.investigations.domain.status import InvestigationStatus
from app.investigations.queue.queue_models import InvestigationQueueItem, InvestigationQueueSummary
from app.investigations.queue.queue_scoring_service import InvestigationQueueScoringService
from app.investigations.queue.sla_policy import InvestigationSLAPolicy


class InvestigationQueueService:
    def __init__(
        self,
        sla_policy: InvestigationSLAPolicy | None = None,
        scoring_service: InvestigationQueueScoringService | None = None,
    ) -> None:
        self.sla_policy = sla_policy or InvestigationSLAPolicy()
        self.scoring_service = scoring_service or InvestigationQueueScoringService()

    def build_queue(
        self,
        cases: list[InvestigationCase],
        now: datetime | None = None,
    ) -> InvestigationQueueSummary:
        now = now or datetime.now(timezone.utc)
        open_cases = [case for case in cases if case.status != InvestigationStatus.CLOSED]

        items = [self._to_queue_item(case, now) for case in open_cases]
        items = sorted(items, key=lambda item: item.queue_score, reverse=True)

        return InvestigationQueueSummary(
            total_open=len(open_cases),
            unassigned=sum(1 for case in open_cases if case.assigned_to is None),
            sla_breached=sum(1 for item in items if item.sla_breached),
            critical_open=sum(1 for case in open_cases if case.priority == InvestigationPriority.CRITICAL),
            items=items,
        )

    def _to_queue_item(self, case: InvestigationCase, now: datetime) -> InvestigationQueueItem:
        sla_due_at = self.sla_policy.due_at(case.created_at, case.priority)
        queue_score, reason = self.scoring_service.score(case, sla_due_at, now)

        return InvestigationQueueItem(
            case_id=case.case_id,
            title=case.title,
            entity_type=case.entity_type,
            entity_id=case.entity_id,
            risk_score=case.risk_score,
            priority=case.priority.value,
            status=case.status.value,
            assigned_to=case.assigned_to,
            created_at=case.created_at,
            sla_due_at=sla_due_at,
            sla_breached=now > sla_due_at,
            queue_score=queue_score,
            reason=reason,
        )
