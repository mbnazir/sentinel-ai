from app.sso.providers.mock_provider import MockSSOProvider
from app.sso.services.provider_factory import SSOProviderFactory


def test_provider_factory_returns_mock_provider() -> None:
    provider = SSOProviderFactory().create("mock")
    assert isinstance(provider, MockSSOProvider)


def test_provider_factory_rejects_unknown_provider() -> None:
    try:
        SSOProviderFactory().create("unknown")
    except ValueError:
        assert True
    else:
        assert False, "Expected unsupported provider error"
