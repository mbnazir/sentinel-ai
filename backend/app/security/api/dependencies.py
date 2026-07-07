from fastapi import Depends, Header, HTTPException

from app.security.domain.principal import Principal
from app.security.domain.roles import Permission
from app.security.services.authorization_service import AuthorizationService
from app.security.services.token_service import TokenService


def get_current_principal(authorization: str | None = Header(default=None)) -> Principal:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header.")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Invalid Authorization header.")

    try:
        return TokenService().decode_access_token(token)
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid access token.") from exc


def require_permission(permission: Permission):
    def dependency(principal: Principal = Depends(get_current_principal)) -> Principal:
        try:
            AuthorizationService().require_permission(principal, permission)
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        return principal

    return dependency
