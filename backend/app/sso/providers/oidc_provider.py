from typing import Any

import httpx

from app.sso.config.oidc_settings import OIDCProviderSettings
from app.sso.domain.sso_profile import SSOProfile
from app.sso.providers.base_provider import BaseSSOProvider


class OIDCProvider(BaseSSOProvider):
    """Generic OIDC provider.

    This class performs authorization-code token exchange and userinfo retrieval.
    Provider-specific classes convert returned claims into Sentinel SSOProfile.
    """

    provider_name = "oidc"

    def __init__(self, settings: OIDCProviderSettings) -> None:
        self.settings = settings
        self.provider_name = settings.provider_name

    async def exchange_code(self, code: str, redirect_uri: str) -> SSOProfile:
        token_payload = await self._exchange_token(code, redirect_uri)
        access_token = token_payload["access_token"]
        claims = await self._fetch_userinfo(access_token)
        return self.claims_to_profile(claims)

    async def _exchange_token(self, code: str, redirect_uri: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                self.settings.token_endpoint,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "client_id": self.settings.client_id,
                    "client_secret": self.settings.client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            return dict(response.json())

    async def _fetch_userinfo(self, access_token: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                self.settings.userinfo_endpoint,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            return dict(response.json())

    def claims_to_profile(self, claims: dict[str, Any]) -> SSOProfile:
        return SSOProfile(
            provider=self.settings.provider_name,
            subject=str(claims.get("sub") or claims.get("oid")),
            email=str(claims.get("email") or claims.get("preferred_username")),
            full_name=str(claims.get("name") or claims.get("email") or "Unknown User"),
            organization_id=self.settings.default_organization_id,
            groups=[str(group) for group in claims.get("groups", [])],
        )
