from dataclasses import replace
from datetime import datetime, timezone

from app.investigations.domain.case import (
    InvestigationCase,
    InvestigationComment,
    InvestigationEvidenceLink,
)
from app.investigations.domain.priority import priority_from_risk_score
from app.investigations.domain.status import InvestigationStatus, can_transition
from app.investigations.services.case_id_generator import CaseIdGenerator
from app.scoring.domain.risk_assessment import RiskAssessment


class InvalidInvestigationTransitionError(ValueError):
    pass


class InvestigationCaseService:
    def __init__(self, id_generator: CaseIdGenerator | None = None) -> None:
        self.id_generator = id_generator or CaseIdGenerator()

    def create_from_risk_assessment(
        self,
        organization_id: str,
        assessment: RiskAssessment,
    ) -> InvestigationCase:
        now = datetime.now(timezone.utc)
        evidence_links = self._evidence_links_from_assessment(assessment)

        return InvestigationCase(
            case_id=self.id_generator.generate(),
            organization_id=organization_id,
            title=f"{assessment.risk_level.value.title()} integrity review for {assessment.entity_type} {assessment.entity_id}",
            entity_type=assessment.entity_type,
            entity_id=assessment.entity_id,
            risk_score=assessment.risk_score,
            priority=priority_from_risk_score(assessment.risk_score),
            status=InvestigationStatus.NEW,
            assigned_to=None,
            created_at=now,
            updated_at=now,
            summary=assessment.summary,
            evidence_links=evidence_links,
            comments=[],
        )

    def assign(self, case: InvestigationCase, assignee_id: str) -> InvestigationCase:
        now = datetime.now(timezone.utc)
        status = case.status
        if status in {InvestigationStatus.NEW, InvestigationStatus.TRIAGED}:
            status = InvestigationStatus.ASSIGNED

        return replace(
            case,
            assigned_to=assignee_id,
            status=status,
            updated_at=now,
        )

    def transition(
        self,
        case: InvestigationCase,
        target_status: InvestigationStatus,
    ) -> InvestigationCase:
        if not can_transition(case.status, target_status):
            raise InvalidInvestigationTransitionError(
                f"Cannot transition investigation from {case.status.value} to {target_status.value}."
            )

        return replace(
            case,
            status=target_status,
            updated_at=datetime.now(timezone.utc),
        )

    def add_comment(
        self,
        case: InvestigationCase,
        author_id: str,
        body: str,
    ) -> InvestigationCase:
        if not body.strip():
            raise ValueError("Comment body cannot be empty.")

        comment = InvestigationComment(
            author_id=author_id,
            body=body.strip(),
            created_at=datetime.now(timezone.utc),
        )

        return replace(
            case,
            comments=[*case.comments, comment],
            updated_at=datetime.now(timezone.utc),
        )

    def _evidence_links_from_assessment(
        self,
        assessment: RiskAssessment,
    ) -> list[InvestigationEvidenceLink]:
        links: list[InvestigationEvidenceLink] = []

        for rule_result in assessment.rule_results:
            for index, evidence in enumerate(rule_result.evidence, start=1):
                links.append(
                    InvestigationEvidenceLink(
                        evidence_id=f"{rule_result.rule_id}-{index}",
                        evidence_type=evidence.evidence_type,
                        source=rule_result.rule_name,
                        summary=rule_result.reason,
                    )
                )

        return links
