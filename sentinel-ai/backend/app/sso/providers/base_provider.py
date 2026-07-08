from abc import ABC, abstractmethod

from app.sso.domain.sso_profile import SSOProfile


class BaseSSOProvider(ABC):
    provider_name: str

    @abstractmethod
    async def exchange_code(self, code: str, redirect_uri: str) -> SSOProfile:
        raise NotImplementedError
