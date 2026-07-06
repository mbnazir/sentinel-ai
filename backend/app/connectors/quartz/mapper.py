from datetime import datetime
from typing import Any

from app.domain.entities.activity import Activity
from app.domain.entities.login_session import LoginSession
from app.domain.value_objects.data_source import map_quartz_data_source


def parse_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def map_login_session(row: dict[str, Any]) -> LoginSession:
    start_time = parse_datetime(row.get("start_date") or row.get("start_time"))
    if start_time is None:
        raise ValueError("Quartz login session is missing start_date/start_time")

    shift_date_raw = row.get("shift_date")
    shift_date = datetime.fromisoformat(shift_date_raw).date() if shift_date_raw else None

    return LoginSession(
        external_id=str(row["id"]),
        agent_external_id=str(row["agent_id"]) if row.get("agent_id") is not None else None,
        supervisor_external_id=str(row["supervisor_id"])
        if row.get("supervisor_id") is not None
        else None,
        shift_date=shift_date,
        start_time=start_time,
        end_time=parse_datetime(row.get("end_date") or row.get("end_time")),
        status=str(row.get("status_id")) if row.get("status_id") is not None else None,
        raw_payload=row,
    )


def map_activity(row: dict[str, Any]) -> Activity:
    start_time = parse_datetime(row.get("start_time"))
    if start_time is None:
        raise ValueError("Quartz activity is missing start_time")

    data_source_id = row.get("data_source_id")
    source = map_quartz_data_source(int(data_source_id) if data_source_id is not None else None)

    return Activity(
        external_id=str(row["id"]),
        login_session_external_id=str(row["login_session_id"]),
        agent_external_id=str(row["agent_id"]) if row.get("agent_id") is not None else None,
        source=source.value,
        source_code=int(data_source_id) if data_source_id is not None else None,
        activity_type=str(row.get("activity_type_id", "unknown")),
        activity_type_external_id=str(row.get("activity_type_id"))
        if row.get("activity_type_id") is not None
        else None,
        start_time=start_time,
        end_time=parse_datetime(row.get("end_time")),
        duration_seconds=int(row.get("duration") or 0),
        inactivity_seconds=int(row.get("inactivity_time") or 0),
        comment=row.get("comment"),
        raw_payload=row,
    )
