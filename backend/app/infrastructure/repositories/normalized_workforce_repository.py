from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entities.activity import Activity
from app.domain.entities.login_session import LoginSession
from app.infrastructure.persistence.models import (
    NormalizedActivityModel,
    NormalizedLoginSessionModel,
)


class NormalizedWorkforceRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def upsert_session(
        self,
        organization_id: int,
        connector_id: int,
        connector_run_id: int | None,
        session: LoginSession,
    ) -> NormalizedLoginSessionModel:
        existing = self.db.execute(
            select(NormalizedLoginSessionModel).where(
                NormalizedLoginSessionModel.connector_id == connector_id,
                NormalizedLoginSessionModel.external_id == session.external_id,
            )
        ).scalar_one_or_none()

        if existing is None:
            existing = NormalizedLoginSessionModel(
                organization_id=organization_id,
                connector_id=connector_id,
                connector_run_id=connector_run_id,
                external_id=session.external_id,
                agent_external_id=session.agent_external_id,
                supervisor_external_id=session.supervisor_external_id,
                shift_date=session.shift_date,
                start_time=session.start_time,
                end_time=session.end_time,
                status=session.status,
                raw_payload=session.raw_payload,
            )
            self.db.add(existing)
            self.db.flush()
            return existing

        existing.connector_run_id = connector_run_id
        existing.agent_external_id = session.agent_external_id
        existing.supervisor_external_id = session.supervisor_external_id
        existing.shift_date = session.shift_date
        existing.start_time = session.start_time
        existing.end_time = session.end_time
        existing.status = session.status
        existing.raw_payload = session.raw_payload
        self.db.flush()
        return existing

    def upsert_activity(
        self,
        organization_id: int,
        connector_id: int,
        connector_run_id: int | None,
        normalized_session_id: int,
        activity: Activity,
    ) -> NormalizedActivityModel:
        existing = self.db.execute(
            select(NormalizedActivityModel).where(
                NormalizedActivityModel.connector_id == connector_id,
                NormalizedActivityModel.external_id == activity.external_id,
            )
        ).scalar_one_or_none()

        if existing is None:
            existing = NormalizedActivityModel(
                organization_id=organization_id,
                connector_id=connector_id,
                connector_run_id=connector_run_id,
                login_session_id=normalized_session_id,
                external_id=activity.external_id,
                login_session_external_id=activity.login_session_external_id,
                agent_external_id=activity.agent_external_id,
                source=activity.source,
                source_code=activity.source_code,
                activity_type=activity.activity_type,
                activity_type_external_id=activity.activity_type_external_id,
                start_time=activity.start_time,
                end_time=activity.end_time,
                duration_seconds=activity.duration_seconds,
                inactivity_seconds=activity.inactivity_seconds,
                comment=activity.comment,
                raw_payload=activity.raw_payload,
            )
            self.db.add(existing)
            self.db.flush()
            return existing

        existing.connector_run_id = connector_run_id
        existing.login_session_id = normalized_session_id
        existing.login_session_external_id = activity.login_session_external_id
        existing.agent_external_id = activity.agent_external_id
        existing.source = activity.source
        existing.source_code = activity.source_code
        existing.activity_type = activity.activity_type
        existing.activity_type_external_id = activity.activity_type_external_id
        existing.start_time = activity.start_time
        existing.end_time = activity.end_time
        existing.duration_seconds = activity.duration_seconds
        existing.inactivity_seconds = activity.inactivity_seconds
        existing.comment = activity.comment
        existing.raw_payload = activity.raw_payload
        self.db.flush()
        return existing
