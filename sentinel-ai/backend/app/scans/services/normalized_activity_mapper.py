from app.infrastructure.persistence.models_normalized import NormalizedActivityModel
from app.timeline.domain.activity_snapshot import ActivitySnapshot
from app.timeline.domain.source import DataSource


class NormalizedActivityMapper:
    def to_snapshot(self, activity: NormalizedActivityModel) -> ActivitySnapshot:
        return ActivitySnapshot(
            external_id=activity.external_id,
            login_session_external_id=activity.login_session_external_id,
            data_source=self._source_to_data_source(activity.source),
            start_time=activity.start_time,
            end_time=activity.end_time,
            duration_seconds=activity.duration_seconds,
            activity_type_id=self._activity_type_to_int(activity.activity_type),
            source_id=None,
            agent_external_id=activity.agent_external_id,
            comment=activity.comment,
        )

    def _source_to_data_source(self, source: str) -> DataSource:
        normalized = source.lower()
        return {
            "phone": DataSource.PHONE,
            "system": DataSource.SYSTEM,
            "agent": DataSource.AGENT,
            "supervisor": DataSource.SUPERVISOR,
            "manager": DataSource.MANAGER,
            "payroll": DataSource.PAYROLL,
        }.get(normalized, DataSource.SYSTEM)

    def _activity_type_to_int(self, value: str) -> int:
        try:
            return int(value)
        except ValueError:
            return abs(hash(value)) % 100000
