from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from datetime import date

from app.application.normalized import NormalizedActivity, NormalizedLoginSession


class WorkforceConnector(ABC):
    @abstractmethod
    async def test_connection(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def iter_sessions(
        self, *, shift_date_from: date, shift_date_to: date
    ) -> AsyncIterator[NormalizedLoginSession]:
        raise NotImplementedError

    @abstractmethod
    async def iter_activities(
        self, *, login_session_ids: list[str]
    ) -> AsyncIterator[NormalizedActivity]:
        raise NotImplementedError
