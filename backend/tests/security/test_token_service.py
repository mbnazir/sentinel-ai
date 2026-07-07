from app.security.domain.principal import Principal
from app.security.domain.roles import Role
from app.security.services.token_service import TokenService


def test_token_round_trip() -> None:
    principal = Principal("U1", "ORG1", "user@example.com", [Role.ADMIN])
    token = TokenService().create_access_token(principal)
    decoded = TokenService().decode_access_token(token)

    assert decoded.user_id == "U1"
    assert decoded.organization_id == "ORG1"
    assert decoded.roles == [Role.ADMIN]
