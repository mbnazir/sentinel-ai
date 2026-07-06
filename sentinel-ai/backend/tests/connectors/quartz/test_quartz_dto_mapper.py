from app.connectors.quartz.mappers.quartz_dto_mapper import QuartzDTOMapper


def test_session_from_api_maps_values() -> None:
    dto = QuartzDTOMapper().session_from_api(
        {
            "id": 100,
            "agent_id": 10,
            "supervisor_id": 20,
            "manager_id": 30,
            "shift_date": "2026-07-01",
            "start_date": "2026-07-01T08:00:00+00:00",
            "end_date": "2026-07-01T17:00:00+00:00",
            "status_id": 1,
        }
    )

    assert dto.id == "100"
    assert dto.agent_id == "10"
    assert dto.shift_date.isoformat() == "2026-07-01"


def test_activity_from_api_maps_duration() -> None:
    dto = QuartzDTOMapper().activity_from_api(
        {
            "id": 1,
            "login_session_id": 100,
            "agent_id": 10,
            "data_source_id": 2,
            "activity_type_id": 1,
            "source_id": 5,
            "start_time": "2026-07-01T08:00:00+00:00",
            "end_time": "2026-07-01T09:00:00+00:00",
            "duration": 3600,
            "comment": "manual edit",
        }
    )

    assert dto.id == "1"
    assert dto.login_session_id == "100"
    assert dto.duration_seconds == 3600
