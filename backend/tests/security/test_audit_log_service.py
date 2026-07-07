from app.audit.services.audit_log_service import AuditEvent


class MemoryAuditRepository:
    def __init__(self) -> None:
        self.events = []

    def save(self, event):
        self.events.append(event)
        return event


def test_audit_event_shape() -> None:
    event = AuditEvent(
        event_type="investigation.case_assigned",
        organization_id="ORG1",
        user_id="U1",
        payload={"case_id": "CASE1"},
    )

    assert event.event_type == "investigation.case_assigned"
    assert event.payload["case_id"] == "CASE1"
