from dataclasses import dataclass
from datetime import date

from app.connectors.quartz.persistence.normalized_ingestion_repository import NormalizedIngestionRepository
from app.connectors.quartz.services.quartz_ingestion_service import QuartzIngestionService


@dataclass(frozen=True)
class PersistedQuartzIngestionResult:
    fetched_sessions: int
    fetched_activities: int
    persisted_sessions: int
    persisted_activities: int


class QuartzPersistedIngestionService:
    def __init__(
        self,
        ingestion_service: QuartzIngestionService,
        repository: NormalizedIngestionRepository,
    ) -> None:
        self.ingestion_service = ingestion_service
        self.repository = repository

    async def ingest_and_persist(
        self,
        organization_id: str,
        shift_date_from: date,
        shift_date_to: date,
    ) -> PersistedQuartzIngestionResult:
        result = await self.ingestion_service.ingest_shift_date_range(shift_date_from, shift_date_to)

        persisted_sessions = self.repository.upsert_sessions(
            organization_id=organization_id,
            connector_type="quartz",
            sessions=result.sessions,
        )
        persisted_activities = self.repository.upsert_activities(
            organization_id=organization_id,
            connector_type="quartz",
            activities=result.activities,
        )

        return PersistedQuartzIngestionResult(
            fetched_sessions=result.session_count,
            fetched_activities=result.activity_count,
            persisted_sessions=persisted_sessions,
            persisted_activities=persisted_activities,
        )
