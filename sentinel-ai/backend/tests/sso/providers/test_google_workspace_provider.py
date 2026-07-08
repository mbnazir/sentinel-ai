from app.sso.config.oidc_settings import GoogleWorkspaceSettings
from app.sso.providers.google_workspace_provider import GoogleWorkspaceProvider


def test_google_claims_to_profile_valid_domain() -> None:
    provider = GoogleWorkspaceProvider(
        GoogleWorkspaceSettings(
            provider_name="google_workspace",
            client_id="client",
            client_secret="secret",
            token_endpoint="https://example.com/token",
            userinfo_endpoint="https://example.com/userinfo",
            issuer="issuer",
            default_organization_id="ORG1",
            scopes=["openid"],
            hosted_domain="example.com",
        )
    )

    profile = provider.claims_to_profile(
        {
            "sub": "SUB1",
            "email": "user@example.com",
            "name": "User Example",
            "hd": "example.com",
        }
    )

    assert profile.provider == "google_workspace"
    assert profile.email == "user@example.com"


def test_google_claims_to_profile_rejects_wrong_domain() -> None:
    provider = GoogleWorkspaceProvider(
        GoogleWorkspaceSettings(
            provider_name="google_workspace",
            client_id="client",
            client_secret="secret",
            token_endpoint="https://example.com/token",
            userinfo_endpoint="https://example.com/userinfo",
            issuer="issuer",
            default_organization_id="ORG1",
            scopes=["openid"],
            hosted_domain="example.com",
        )
    )

    try:
        provider.claims_to_profile({"sub": "SUB1", "email": "user@other.com", "hd": "other.com"})
    except ValueError:
        assert True
    else:
        assert False, "Expected domain validation error"
