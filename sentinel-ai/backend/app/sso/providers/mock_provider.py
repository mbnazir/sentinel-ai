from app.sso.domain.sso_profile import SSOProfile
from app.sso.providers.base_provider import BaseSSOProvider


class MockSSOProvider(BaseSSOProvider):
    provider_name = "mock"

    async def exchange_code(self, code: str, redirect_uri: str) -> SSOProfile:
        return SSOProfile(
            provider=self.provider_name,
            subject=f"mock-subject-{code}",
            email="mock.user@sentinel.local",
            full_name="Mock User",
            organization_id="ORG-DEV",
            groups=["Sentinel-Admin"],
        )
