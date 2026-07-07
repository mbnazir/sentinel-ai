from typing import Any

from app.sso.config.oidc_settings import AzureADSettings
from app.sso.domain.sso_profile import SSOProfile
from app.sso.providers.oidc_provider import OIDCProvider


class AzureADProvider(OIDCProvider):
    provider_name = "azure_ad"

    def __init__(self, settings: AzureADSettings) -> None:
        super().__init__(settings)
        self.azure_settings = settings

    def claims_to_profile(self, claims: dict[str, Any]) -> SSOProfile:
        return SSOProfile(
            provider=self.provider_name,
            subject=str(claims.get("oid") or claims.get("sub")),
            email=str(claims.get("preferred_username") or claims.get("email")),
            full_name=str(claims.get("name") or claims.get("preferred_username")),
            organization_id=self.settings.default_organization_id,
            groups=[str(group) for group in claims.get("groups", [])],
        )
