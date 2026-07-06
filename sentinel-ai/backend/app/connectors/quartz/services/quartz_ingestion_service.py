from dataclasses import dataclass
from datetime import date

from app.connectors.quartz.client.quartz_api_client import QuartzAPIClient
from app.connectors.quartz.mappers.quartz_dto_mapper import QuartzDTOMapper
from app.connectors.quartz.mappers.quartz_normalized_mapper import QuartzNormalizedMapper
from app.domain.entities.activity import Activity
from app.domain.entities.login_session import LoginSession


@dataclass(frozen=True)
class QuartzIngestionResult:
    sessions: list[LoginSession]
    activities: list[Activity]
    session_count: int
    activity_count: int


class QuartzIngestionService:
    def __init__(
        self,
        client: QuartzAPIClient,
        dto_mapper: QuartzDTOMapper | None = None,
        normalized_mapper: QuartzNormalizedMapper | None = None,
    ) -> None:
        self.client = client
        self.dto_mapper = dto_mapper or QuartzDTOMapper()
        self.normalized_mapper = normalized_mapper or QuartzNormalizedMapper()

    async def ingest_shift_date_range(
        self,
        shift_date_from: date,
        shift_date_to: date,
    ) -> QuartzIngestionResult:
        session_dtos = []
        cursor = None

        while True:
            page = await self.client.fetch_sessions_page(shift_date_from, shift_date_to, cursor)
            session_dtos.extend(self.dto_mapper.session_from_api(row) for row in page.items)
            cursor = page.next_cursor
            if not cursor:
                break

        session_ids = [dto.id for dto in session_dtos]
        activity_rows = await self.client.fetch_activities_batch(session_ids)
        activity_dtos = [self.dto_mapper.activity_from_api(row) for row in activity_rows]

        sessions = [self.normalized_mapper.session_to_domain(dto) for dto in session_dtos]
        activities = [self.normalized_mapper.activity_to_domain(dto) for dto in activity_dtos]

        return QuartzIngestionResult(
            sessions=sessions,
            activities=activities,
            session_count=len(sessions),
            activity_count=len(activities),
        )
