from dataclasses import dataclass


@dataclass(frozen=True)
class OIDCProviderSettings:
    provider_name: str
    client_id: str
    client_secret: str
    token_endpoint: str
    userinfo_endpoint: str
    issuer: str
    default_organization_id: str
    scopes: list[str]


@dataclass(frozen=True)
class AzureADSettings(OIDCProviderSettings):
    tenant_id: str


@dataclass(frozen=True)
class GoogleWorkspaceSettings(OIDCProviderSettings):
    hosted_domain: str | None = None
