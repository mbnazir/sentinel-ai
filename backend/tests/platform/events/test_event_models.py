from app.platform.events.event_models import DomainEvent, EventType


def test_domain_event_create_sets_id_and_type() -> None:
    event = DomainEvent.create(
        event_type=EventType.ANOMALY_DETECTED,
        organization_id="ORG1",
        payload={"entity_id": "A1"},
    )

    assert event.event_id.startswith("EVT-")
    assert event.event_type == EventType.ANOMALY_DETECTED
    assert event.payload["entity_id"] == "A1"
