from app.investigations.domain.case import InvestigationCase
from app.investigations.workspace.workspace_models import WorkspaceTimelineEvent


class WorkspaceTimelineBuilder:
    """Builds a case-level investigation timeline from case data."""

    def build(self, case: InvestigationCase) -> list[WorkspaceTimelineEvent]:
        events: list[WorkspaceTimelineEvent] = [
            WorkspaceTimelineEvent(
                event_id=f"{case.case_id}-created",
                event_type="case_created",
                title="Case created",
                description=f"Investigation case created for {case.entity_type} {case.entity_id}.",
                occurred_at=case.created_at,
                actor_id=None,
                metadata={"risk_score": case.risk_score, "priority": case.priority.value},
            )
        ]

        if case.assigned_to:
            events.append(
                WorkspaceTimelineEvent(
                    event_id=f"{case.case_id}-assigned",
                    event_type="case_assigned",
                    title="Case assigned",
                    description=f"Case assigned to {case.assigned_to}.",
                    occurred_at=case.updated_at or case.created_at,
                    actor_id=case.assigned_to,
                    metadata={},
                )
            )

        for index, link in enumerate(case.evidence_links, start=1):
            events.append(
                WorkspaceTimelineEvent(
                    event_id=f"{case.case_id}-evidence-{index}",
                    event_type="evidence_attached",
                    title=f"Evidence attached: {link.evidence_type}",
                    description=link.summary,
                    occurred_at=case.updated_at or case.created_at,
                    actor_id=None,
                    metadata={"evidence_id": link.evidence_id, "source": link.source},
                )
            )

        for index, comment in enumerate(case.comments, start=1):
            events.append(
                WorkspaceTimelineEvent(
                    event_id=f"{case.case_id}-note-{index}",
                    event_type="note_added",
                    title="Investigation note added",
                    description=comment.body,
                    occurred_at=comment.created_at,
                    actor_id=comment.author_id,
                    metadata={},
                )
            )

        return sorted(events, key=lambda item: item.occurred_at)
