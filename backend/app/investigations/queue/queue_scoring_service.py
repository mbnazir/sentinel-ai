from datetime import datetime, timezone

from app.investigations.domain.case import InvestigationCase
from app.investigations.domain.priority import InvestigationPriority


class InvestigationQueueScoringService:
    """Calculates operational queue priority.

    Queue score is different from risk score. It combines risk, SLA urgency, assignment state,
    and case age so investigators know what to work first.
    """

    def score(self, case: InvestigationCase, sla_due_at: datetime, now: datetime | None = None) -> tuple[int, str]:
        now = now or datetime.now(timezone.utc)
        score = case.risk_score
        reasons = [f"risk score {case.risk_score}"]

        if case.priority == InvestigationPriority.CRITICAL:
            score += 30
            reasons.append("critical priority")
        elif case.priority == InvestigationPriority.HIGH:
            score += 20
            reasons.append("high priority")
        elif case.priority == InvestigationPriority.MEDIUM:
            score += 10
            reasons.append("medium priority")

        if case.assigned_to is None:
            score += 15
            reasons.append("unassigned")

        if now > sla_due_at:
            score += 40
            reasons.append("SLA breached")
        else:
            hours_left = (sla_due_at - now).total_seconds() / 3600
            if hours_left <= 4:
                score += 20
                reasons.append("SLA due soon")
            elif hours_left <= 24:
                score += 10
                reasons.append("SLA approaching")

        age_hours = (now - case.created_at).total_seconds() / 3600
        if age_hours >= 72:
            score += 10
            reasons.append("older than 72 hours")

        return min(200, score), ", ".join(reasons)
