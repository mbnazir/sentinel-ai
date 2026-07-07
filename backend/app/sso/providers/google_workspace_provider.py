from typing import Any

from app.sso.config.oidc_settings import GoogleWorkspaceSettings
from app.sso.domain.sso_profile import SSOProfile
from app.sso.providers.oidc_provider import OIDCProvider


class GoogleWorkspaceProvider(OIDCProvider):
    provider_name = "google_workspace"

    def __init__(self, settings: GoogleWorkspaceSettings) -> None:
        super().__init__(settings)
        self.google_settings = settings

    def claims_to_profile(self, claims: dict[str, Any]) -> SSOProfile:
        hosted_domain = claims.get("hd")
        if self.google_settings.hosted_domain and hosted_domain != self.google_settings.hosted_domain:
            raise ValueError("Google Workspace hosted domain does not match configured domain.")

        return SSOProfile(
            provider=self.provider_name,
            subject=str(claims.get("sub")),
            email=str(claims.get("email")),
            full_name=str(claims.get("name") or claims.get("email")),
            organization_id=self.settings.default_organization_id,
            groups=[str(group) for group in claims.get("groups", [])],
        )
