from datetime import datetime, timedelta

from app.investigations.domain.priority import InvestigationPriority


class InvestigationSLAPolicy:
    """Defines SLA windows by case priority."""

    def due_at(self, created_at: datetime, priority: InvestigationPriority) -> datetime:
        hours = {
            InvestigationPriority.CRITICAL: 4,
            InvestigationPriority.HIGH: 24,
            InvestigationPriority.MEDIUM: 72,
            InvestigationPriority.LOW: 168,
        }[priority]
        return created_at + timedelta(hours=hours)
