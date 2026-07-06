from app.connectors.quartz.mapper import map_activity


def test_quartz_activity_source_mapping() -> None:
    activity = map_activity(
        {
            "id": 10,
            "login_session_id": 20,
            "agent_id": 30,
            "data_source_id": 3,
            "activity_type_id": 5,
            "start_time": "2026-07-01T08:00:00+00:00",
            "end_time": "2026-07-01T09:00:00+00:00",
            "duration": 3600,
            "inactivity_time": 0,
            "comment": "approved",
        }
    )

    assert activity.source == "supervisor"
    assert activity.duration_seconds == 3600
    assert activity.login_session_external_id == "20"
