from app.security.domain.principal import Principal
from app.security.domain.roles import Permission, Role
from app.security.services.authorization_service import AuthorizationService


def test_investigator_can_generate_ai_narrative() -> None:
    principal = Principal("U1", "ORG1", "investigator@example.com", [Role.INVESTIGATOR])
    assert AuthorizationService().has_permission(principal, Permission.GENERATE_AI_NARRATIVE) is True


def test_supervisor_cannot_assign_cases() -> None:
    principal = Principal("U1", "ORG1", "supervisor@example.com", [Role.SUPERVISOR])
    assert AuthorizationService().has_permission(principal, Permission.ASSIGN_CASES) is False
