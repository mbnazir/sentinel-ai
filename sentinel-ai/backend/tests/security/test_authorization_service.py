from app.security.domain.principal import Principal
from app.security.domain.roles import Permission, Role
from app.security.services.authorization_service import AuthorizationService


def test_admin_has_all_permissions() -> None:
    principal = Principal("U1", "ORG1", "admin@example.com", [Role.ADMIN])
    assert AuthorizationService().has_permission(principal, Permission.MANAGE_USERS) is True


def test_read_only_cannot_manage_cases() -> None:
    principal = Principal("U1", "ORG1", "readonly@example.com", [Role.READ_ONLY])
    assert AuthorizationService().has_permission(principal, Permission.MANAGE_CASES) is False
