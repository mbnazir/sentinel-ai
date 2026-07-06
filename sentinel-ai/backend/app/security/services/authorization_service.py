from app.security.domain.principal import Principal
from app.security.domain.roles import Permission, role_has_permission


class AuthorizationService:
    def has_permission(self, principal: Principal, permission: Permission) -> bool:
        return any(role_has_permission(role, permission) for role in principal.roles)

    def require_permission(self, principal: Principal, permission: Permission) -> None:
        if not self.has_permission(principal, permission):
            raise PermissionError(f"Permission denied: {permission.value}")
