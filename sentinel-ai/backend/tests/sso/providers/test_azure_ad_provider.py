from app.sso.config.oidc_settings import AzureADSettings
from app.sso.providers.azure_ad_provider import AzureADProvider


def test_azure_claims_to_profile() -> None:
    provider = AzureADProvider(
        AzureADSettings(
            provider_name="azure_ad",
            tenant_id="tenant",
            client_id="client",
            client_secret="secret",
            token_endpoint="https://example.com/token",
            userinfo_endpoint="https://example.com/userinfo",
            issuer="issuer",
            default_organization_id="ORG1",
            scopes=["openid"],
        )
    )

    profile = provider.claims_to_profile(
        {
            "oid": "OID1",
            "preferred_username": "user@example.com",
            "name": "User Example",
            "groups": ["Sentinel-Investigator"],
        }
    )

    assert profile.provider == "azure_ad"
    assert profile.subject == "OID1"
    assert profile.email == "user@example.com"
    assert profile.groups == ["Sentinel-Investigator"]
