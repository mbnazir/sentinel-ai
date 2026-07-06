import os

from app.sso.config.oidc_settings import AzureADSettings, GoogleWorkspaceSettings
from app.sso.providers.azure_ad_provider import AzureADProvider
from app.sso.providers.base_provider import BaseSSOProvider
from app.sso.providers.google_workspace_provider import GoogleWorkspaceProvider
from app.sso.providers.mock_provider import MockSSOProvider


class SSOProviderFactory:
    def create(self, provider_name: str) -> BaseSSOProvider:
        if provider_name == "mock":
            return MockSSOProvider()

        if provider_name == "azure_ad":
            tenant_id = os.getenv("AZURE_AD_TENANT_ID", "")
            return AzureADProvider(
                AzureADSettings(
                    provider_name="azure_ad",
                    tenant_id=tenant_id,
                    client_id=os.getenv("AZURE_AD_CLIENT_ID", ""),
                    client_secret=os.getenv("AZURE_AD_CLIENT_SECRET", ""),
                    token_endpoint=f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token",
                    userinfo_endpoint="https://graph.microsoft.com/oidc/userinfo",
                    issuer=f"https://login.microsoftonline.com/{tenant_id}/v2.0",
                    default_organization_id=os.getenv("AZURE_AD_DEFAULT_ORG", "ORG-DEFAULT"),
                    scopes=["openid", "profile", "email"],
                )
            )

        if provider_name == "google_workspace":
            return GoogleWorkspaceProvider(
                GoogleWorkspaceSettings(
                    provider_name="google_workspace",
                    client_id=os.getenv("GOOGLE_CLIENT_ID", ""),
                    client_secret=os.getenv("GOOGLE_CLIENT_SECRET", ""),
                    token_endpoint="https://oauth2.googleapis.com/token",
                    userinfo_endpoint="https://openidconnect.googleapis.com/v1/userinfo",
                    issuer="https://accounts.google.com",
                    default_organization_id=os.getenv("GOOGLE_DEFAULT_ORG", "ORG-DEFAULT"),
                    scopes=["openid", "profile", "email"],
                    hosted_domain=os.getenv("GOOGLE_WORKSPACE_DOMAIN"),
                )
            )

        raise ValueError(f"Unsupported SSO provider: {provider_name}")
