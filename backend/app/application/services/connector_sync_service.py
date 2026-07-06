from datetime import date

from sqlalchemy.orm import Session

from app.application.dto.import_summary import ImportSummary
from app.application.interfaces.connector import Connector
from app.infrastructure.repositories.normalized_workforce_repository import (
    NormalizedWorkforceRepository,
)


class ConnectorSyncService:
    def __init__(
        self,
        db: Session,
        connector: Connector,
        organization_id: int,
        connector_id: int,
        connector_run_id: int | None = None,
    ) -> None:
        self.db = db
        self.connector = connector
        self.organization_id = organization_id
        self.connector_id = connector_id
        self.connector_run_id = connector_run_id
        self.repository = NormalizedWorkforceRepository(db)

    async def synchronize_shift_dates(
        self,
        shift_date_from: date,
        shift_date_to: date,
    ) -> ImportSummary:
        sessions = await self.connector.get_sessions(shift_date_from, shift_date_to)
        session_ids = [session.external_id for session in sessions]
        activities = await self.connector.get_activities(session_ids) if session_ids else []

        normalized_session_id_by_external_id: dict[str, int] = {}
        for session in sessions:
            persisted = self.repository.upsert_session(
                organization_id=self.organization_id,
                connector_id=self.connector_id,
                connector_run_id=self.connector_run_id,
                session=session,
            )
            normalized_session_id_by_external_id[session.external_id] = persisted.id

        activities_imported = 0
        activities_skipped = 0
        for activity in activities:
            normalized_session_id = normalized_session_id_by_external_id.get(
                activity.login_session_external_id
            )
            if normalized_session_id is None:
                activities_skipped += 1
                continue
            self.repository.upsert_activity(
                organization_id=self.organization_id,
                connector_id=self.connector_id,
                connector_run_id=self.connector_run_id,
                normalized_session_id=normalized_session_id,
                activity=activity,
            )
            activities_imported += 1

        self.db.commit()

        return ImportSummary(
            connector_id=self.connector_id,
            connector_run_id=self.connector_run_id,
            sessions_imported=len(sessions),
            activities_imported=activities_imported,
            activities_skipped=activities_skipped,
        )
