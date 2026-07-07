from app.audit.services.audit_log_service import AuditEvent
from app.infrastructure.persistence.models import AuditLogModel
from sqlalchemy.orm import Session


class AuditLogRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, event: AuditEvent) -> AuditEvent:
        self.session.add(
            AuditLogModel(
                organization_id=int(event.organization_id) if event.organization_id and event.organization_id.isdigit() else None,
                user_id=int(event.user_id) if event.user_id and event.user_id.isdigit() else None,
                event_type=event.event_type,
                payload={
                    **event.payload,
                    "organization_id_raw": event.organization_id,
                    "user_id_raw": event.user_id,
                    "created_at": event.created_at.isoformat(),
                },
            )
        )
        self.session.commit()
        return event
