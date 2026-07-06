from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class AuditEvent:
    event_type: str
    organization_id: str | None
    user_id: str | None
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class AuditLogService:
    """Audit log service scaffold.

    Milestone 15 keeps this dependency-light. Persistence-backed audit logging should be
    wired to the existing audit_logs table in the next hardening pass.
    """

    def record(self, event: AuditEvent) -> AuditEvent:
        return event
