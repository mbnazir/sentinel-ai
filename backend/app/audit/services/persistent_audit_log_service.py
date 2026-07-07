from app.audit.services.audit_log_service import AuditEvent
from app.infrastructure.persistence.repositories.audit_log_repository import AuditLogRepository


class PersistentAuditLogService:
    def __init__(self, repository: AuditLogRepository) -> None:
        self.repository = repository

    def record(self, event: AuditEvent) -> AuditEvent:
        return self.repository.save(event)
