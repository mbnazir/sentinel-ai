from datetime import date

from app.application.interfaces.connector import Connector
from app.connectors.quartz.config import QuartzConnectorConfig
from app.connectors.quartz.mapper import map_activity, map_login_session
from app.connectors.quartz.rest_client import QuartzRestClient
from app.domain.entities.activity import Activity
from app.domain.entities.login_session import LoginSession


class QuartzConnector(Connector):
    """Quartz REST connector.

    The connector consumes Quartz APIs and converts their payloads into Sentinel's normalized domain model.
    Direct read-only MySQL ingestion will be added as a legacy adapter, not as the default path.
    """

    def __init__(self, config: QuartzConnectorConfig, client: QuartzRestClient | None = None) -> None:
        self.config = config
        self.client = client or QuartzRestClient(config)

    async def test_connection(self) -> bool:
        # Health endpoint naming will be finalized when Quartz exposes the integration API.
        return True

    async def get_sessions(
        self,
        shift_date_from: date,
        shift_date_to: date,
    ) -> list[LoginSession]:
        rows = await self.client.get_sessions(shift_date_from, shift_date_to)
        return [map_login_session(row) for row in rows]

    async def get_activities(
        self,
        login_session_external_ids: list[str],
    ) -> list[Activity]:
        rows = await self.client.get_activities(login_session_external_ids)
        return [map_activity(row) for row in rows]
