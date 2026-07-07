from datetime import date, datetime
from typing import Any

from app.connectors.quartz.client.quartz_api_models import QuartzActivityDTO, QuartzSessionDTO


class QuartzDTOMapper:
    def session_from_api(self, row: dict[str, Any]) -> QuartzSessionDTO:
        return QuartzSessionDTO(
            id=str(row["id"]),
            agent_id=str(row["agent_id"]) if row.get("agent_id") is not None else None,
            supervisor_id=str(row["supervisor_id"]) if row.get("supervisor_id") is not None else None,
            manager_id=str(row["manager_id"]) if row.get("manager_id") is not None else None,
            shift_date=self._date(row.get("shift_date")),
            start_date=self._datetime(row["start_date"]),
            end_date=self._optional_datetime(row.get("end_date")),
            status_id=int(row["status_id"]) if row.get("status_id") is not None else None,
            raw=row,
        )

    def activity_from_api(self, row: dict[str, Any]) -> QuartzActivityDTO:
        return QuartzActivityDTO(
            id=str(row["id"]),
            login_session_id=str(row["login_session_id"]),
            agent_id=str(row["agent_id"]) if row.get("agent_id") is not None else None,
            data_source_id=int(row["data_source_id"]),
            activity_type_id=int(row["activity_type_id"]),
            source_id=int(row["source_id"]) if row.get("source_id") is not None else None,
            start_time=self._datetime(row["start_time"]),
            end_time=self._optional_datetime(row.get("end_time")),
            duration_seconds=int(row.get("duration") or row.get("duration_seconds") or 0),
            comment=str(row["comment"]) if row.get("comment") else None,
            raw=row,
        )

    def _datetime(self, value: str | datetime) -> datetime:
        if isinstance(value, datetime):
            return value
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))

    def _optional_datetime(self, value: str | datetime | None) -> datetime | None:
        if value is None:
            return None
        return self._datetime(value)

    def _date(self, value: str | date | None) -> date | None:
        if value is None:
            return None
        if isinstance(value, date):
            return value
        return date.fromisoformat(str(value))
