from app.infrastructure.persistence.repositories.investigation_repository import InvestigationRepository
from app.investigations.workspace.workspace_models import (
    InvestigationWorkspace,
    WorkspaceEvidenceItem,
    WorkspaceNote,
)
from app.investigations.workspace.workspace_timeline_builder import WorkspaceTimelineBuilder


class InvestigationWorkspaceService:
    def __init__(
        self,
        repository: InvestigationRepository,
        timeline_builder: WorkspaceTimelineBuilder | None = None,
    ) -> None:
        self.repository = repository
        self.timeline_builder = timeline_builder or WorkspaceTimelineBuilder()

    def get_workspace(self, case_id: str) -> InvestigationWorkspace:
        case = self.repository.get_by_case_id(case_id)
        if case is None:
            raise ValueError(f"Investigation case {case_id} not found.")

        return InvestigationWorkspace(
            case_id=case.case_id,
            title=case.title,
            entity_type=case.entity_type,
            entity_id=case.entity_id,
            risk_score=case.risk_score,
            priority=case.priority.value,
            status=case.status.value,
            assigned_to=case.assigned_to,
            summary=case.summary,
            evidence=[
                WorkspaceEvidenceItem(
                    evidence_id=link.evidence_id,
                    evidence_type=link.evidence_type,
                    source=link.source,
                    summary=link.summary,
                    severity=self._severity_from_evidence(link.evidence_type),
                )
                for link in case.evidence_links
            ],
            notes=[
                WorkspaceNote(
                    author_id=comment.author_id,
                    body=comment.body,
                    created_at=comment.created_at,
                )
                for comment in case.comments
            ],
            timeline=self.timeline_builder.build(case),
        )

    def _severity_from_evidence(self, evidence_type: str) -> str:
        normalized = evidence_type.lower()
        if "anomaly" in normalized:
            return "high"
        if "payroll" in normalized:
            return "critical"
        if "manual" in normalized or "override" in normalized:
            return "high"
        return "info"
