from datetime import datetime
from typing import Any
from app.timeline.domain.activity_snapshot import ActivitySnapshot
from app.timeline.domain.source import DataSource

class ActivitySnapshotMapper:
    def from_mapping(self, row: dict[str, Any]) -> ActivitySnapshot:
        return ActivitySnapshot(
            external_id=str(row["external_id"]),
            login_session_external_id=str(row["login_session_external_id"]),
            data_source=DataSource(int(row["data_source_id"])),
            start_time=self._dt(row["start_time"]),
            end_time=self._dt(row.get("end_time")) if row.get("end_time") else None,
            duration_seconds=int(row.get("duration_seconds") or 0),
            activity_type_id=int(row["activity_type_id"]),
            source_id=int(row["source_id"]) if row.get("source_id") is not None else None,
            agent_external_id=str(row["agent_external_id"]) if row.get("agent_external_id") else None,
            comment=str(row["comment"]) if row.get("comment") else None,
        )

    def _dt(self, value: Any) -> datetime:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            return datetime.fromisoformat(value)
        raise TypeError("Expected datetime or ISO datetime string.")
