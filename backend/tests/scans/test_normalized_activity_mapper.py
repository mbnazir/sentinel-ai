from datetime import datetime, timezone

from app.scans.services.normalized_activity_mapper import NormalizedActivityMapper
from app.timeline.domain.source import DataSource


class FakeActivity:
    external_id = "A1"
    login_session_external_id = "LS1"
    source = "Agent"
    activity_type = "1"
    start_time = datetime(2026, 7, 1, 8, tzinfo=timezone.utc)
    end_time = datetime(2026, 7, 1, 9, tzinfo=timezone.utc)
    duration_seconds = 3600
    agent_external_id = "AG1"
    comment = "manual"


def test_maps_normalized_activity_to_snapshot() -> None:
    snapshot = NormalizedActivityMapper().to_snapshot(FakeActivity())

    assert snapshot.external_id == "A1"
    assert snapshot.data_source == DataSource.AGENT
    assert snapshot.duration_seconds == 3600
