from datetime import datetime, timezone

from app.timeline.api.mapper import build_timeline_visualization_response


class FakeActivity:
    def __init__(self):
        self.external_id = "A1"
        self.login_session_external_id = "LS-1"
        self.data_source_id = 2
        self.source_label = "Agent"
        self.activity_type_id = 1
        self.activity_type_label = "Work"
        self.start_time = datetime(2026, 7, 1, 8, 0, tzinfo=timezone.utc)
        self.end_time = datetime(2026, 7, 1, 9, 0, tzinfo=timezone.utc)
        self.duration_seconds = 3600
        self.risk_type = "inserted"
        self.risk_note = "Inserted manual activity."


def test_build_timeline_visualization_response_groups_lanes_and_evidence() -> None:
    response = build_timeline_visualization_response("LS-1", [FakeActivity()])

    assert response["case_id"] == "LS-1"
    assert response["lanes"][0]["source"] == "Agent"
    assert response["lanes"][0]["activities"][0]["id"] == "A1"
    assert response["evidence"][0]["activity_id"] == "A1"
