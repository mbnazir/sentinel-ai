from dataclasses import replace

from app.anomaly.cases.anomaly_case_evidence_builder import AnomalyCaseEvidenceBuilder
from app.anomaly.domain.anomaly_models import AnomalyScore, AnomalySeverity
from app.infrastructure.persistence.repositories.investigation_repository import InvestigationRepository
from app.investigations.domain.case import InvestigationCase
from app.investigations.domain.priority import priority_from_risk_score
from app.investigations.domain.status import InvestigationStatus
from app.investigations.services.case_id_generator import CaseIdGenerator


class AnomalyCaseAttachmentService:
    """Creates or updates investigation cases for anomaly findings."""

    def __init__(
        self,
        repository: InvestigationRepository,
        evidence_builder: AnomalyCaseEvidenceBuilder | None = None,
        case_id_generator: CaseIdGenerator | None = None,
    ) -> None:
        self.repository = repository
        self.evidence_builder = evidence_builder or AnomalyCaseEvidenceBuilder()
        self.case_id_generator = case_id_generator or CaseIdGenerator()

    def attach_or_create_case(
        self,
        organization_id: str,
        anomaly_score: AnomalyScore,
        minimum_score: int = 61,
    ) -> InvestigationCase | None:
        if anomaly_score.severity == AnomalySeverity.NONE or anomaly_score.score < minimum_score:
            return None

        existing_case = self._find_open_case(organization_id, anomaly_score.entity_type, anomaly_score.entity_id)
        evidence_links = self.evidence_builder.build_links(anomaly_score)

        if existing_case is not None:
            existing_ids = {link.evidence_id for link in existing_case.evidence_links}
            new_links = [link for link in evidence_links if link.evidence_id not in existing_ids]
            updated = replace(
                existing_case,
                risk_score=max(existing_case.risk_score, anomaly_score.score),
                priority=priority_from_risk_score(max(existing_case.risk_score, anomaly_score.score)),
                evidence_links=[*existing_case.evidence_links, *new_links],
                summary=f"{existing_case.summary}\nAdditional anomaly evidence attached: {anomaly_score.summary}",
            )
            return self.repository.save(updated)

        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        case = InvestigationCase(
            case_id=self.case_id_generator.generate(),
            organization_id=organization_id,
            title=f"{anomaly_score.severity.value.title()} behavior anomaly review for {anomaly_score.entity_type} {anomaly_score.entity_id}",
            entity_type=anomaly_score.entity_type,
            entity_id=anomaly_score.entity_id,
            risk_score=anomaly_score.score,
            priority=priority_from_risk_score(anomaly_score.score),
            status=InvestigationStatus.NEW,
            assigned_to=None,
            created_at=now,
            updated_at=now,
            summary=anomaly_score.summary,
            evidence_links=evidence_links,
            comments=[],
        )
        return self.repository.save(case)

    def _find_open_case(
        self,
        organization_id: str,
        entity_type: str,
        entity_id: str,
    ) -> InvestigationCase | None:
        for case in self.repository.list(organization_id=organization_id, limit=500):
            if (
                case.entity_type == entity_type
                and case.entity_id == entity_id
                and case.status != InvestigationStatus.CLOSED
            ):
                return case
        return None
