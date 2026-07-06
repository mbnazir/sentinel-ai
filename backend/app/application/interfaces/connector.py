from abc import ABC, abstractmethod
from datetime import date

from app.domain.entities.activity import Activity
from app.domain.entities.login_session import LoginSession


class Connector(ABC):
    @abstractmethod
    async def test_connection(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def get_sessions(self, shift_date_from: date, shift_date_to: date) -> list[LoginSession]:
        raise NotImplementedError

    @abstractmethod
    async def get_activities(self, login_session_external_ids: list[str]) -> list[Activity]:
        raise NotImplementedError
