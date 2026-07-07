from sqlalchemy.orm import Session

from app.domain.entities.activity import Activity
from app.domain.entities.login_session import LoginSession
from app.infrastructure.persistence.models_normalized import (
    NormalizedActivityModel,
    NormalizedLoginSessionModel,
)


class NormalizedIngestionRepository:
    """Idempotent normalized store writer for connector output."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert_sessions(
        self,
        organization_id: str,
        connector_type: str,
        sessions: list[LoginSession],
    ) -> int:
        count = 0
        for item in sessions:
            model = (
                self.session.query(NormalizedLoginSessionModel)
                .filter_by(organization_id=organization_id, external_id=item.external_id)
                .one_or_none()
            )
            if model is None:
                model = NormalizedLoginSessionModel(
                    organization_id=organization_id,
                    external_id=item.external_id,
                )
                self.session.add(model)

            model.connector_type = connector_type
            model.agent_external_id = item.agent_external_id
            model.supervisor_external_id = item.supervisor_external_id
            model.shift_date = item.shift_date
            model.start_time = item.start_time
            model.end_time = item.end_time
            model.status = item.status
            count += 1

        self.session.commit()
        return count

    def upsert_activities(
        self,
        organization_id: str,
        connector_type: str,
        activities: list[Activity],
    ) -> int:
        count = 0
        for item in activities:
            model = (
                self.session.query(NormalizedActivityModel)
                .filter_by(organization_id=organization_id, external_id=item.external_id)
                .one_or_none()
            )
            if model is None:
                model = NormalizedActivityModel(
                    organization_id=organization_id,
                    external_id=item.external_id,
                )
                self.session.add(model)

            model.connector_type = connector_type
            model.login_session_external_id = item.login_session_external_id
            model.agent_external_id = item.agent_external_id
            model.source = item.source
            model.activity_type = item.activity_type
            model.start_time = item.start_time
            model.end_time = item.end_time
            model.duration_seconds = item.duration_seconds
            model.comment = item.comment
            count += 1

        self.session.commit()
        return count
