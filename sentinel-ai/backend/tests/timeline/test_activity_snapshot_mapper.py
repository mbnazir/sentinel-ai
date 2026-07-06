from app.timeline.domain.source import DataSource
from app.timeline.services.activity_snapshot_mapper import ActivitySnapshotMapper

def test_activity_snapshot_mapper_maps_normalized_activity_row() -> None:
    row = {
        "external_id": "A-1",
        "login_session_external_id": "LS-1",
        "data_source_id": 2,
        "start_time": "2026-07-01T08:00:00",
        "end_time": "2026-07-01T09:00:00",
        "duration_seconds": 3600,
        "activity_type_id": 1,
        "source_id": 10,
        "agent_external_id": "100",
        "comment": "manual correction",
    }
    snapshot = ActivitySnapshotMapper().from_mapping(row)
    assert snapshot.external_id == "A-1"
    assert snapshot.data_source == DataSource.AGENT
    assert snapshot.duration_seconds == 3600
