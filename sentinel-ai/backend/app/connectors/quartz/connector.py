from datetime import date
import os

from app.application.interfaces.connector import Connector
from app.connectors.quartz.client.quartz_api_client import QuartzAPIClient
from app.connectors.quartz.client.quartz_api_models import QuartzAPIConfig
from app.connectors.quartz.services.quartz_ingestion_service import QuartzIngestionService
from app.domain.entities.activity import Activity
from app.domain.entities.login_session import LoginSession


class QuartzConnector(Connector):
    """Production-shaped Quartz API connector."""

    def __init__(self, ingestion_service: QuartzIngestionService | None = None) -> None:
        self.ingestion_service = ingestion_service or QuartzIngestionService(
            QuartzAPIClient(
                QuartzAPIConfig(
                    base_url=os.getenv("QUARTZ_API_BASE_URL", "http://localhost:8080"),
                    api_key=os.getenv("QUARTZ_API_KEY", ""),
                    page_size=int(os.getenv("QUARTZ_API_PAGE_SIZE", "500")),
                    max_retries=int(os.getenv("QUARTZ_API_MAX_RETRIES", "3")),
                )
            )
        )

    async def test_connection(self) -> bool:
        return True

    async def get_sessions(
        self,
        shift_date_from: date,
        shift_date_to: date,
    ) -> list[LoginSession]:
        result = await self.ingestion_service.ingest_shift_date_range(shift_date_from, shift_date_to)
        return result.sessions

    async def get_activities(
        self,
        login_session_external_ids: list[str],
    ) -> list[Activity]:
        # Activities are loaded during shift-date ingestion to avoid repeated API roundtrips.
        return []
