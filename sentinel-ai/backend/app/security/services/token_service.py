from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt

from app.core.config.settings import settings
from app.security.domain.principal import Principal
from app.security.domain.roles import Role


class TokenService:
    def create_access_token(self, principal: Principal) -> str:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
        payload: dict[str, Any] = {
            "sub": principal.user_id,
            "organization_id": principal.organization_id,
            "email": principal.email,
            "roles": [role.value for role in principal.roles],
            "exp": expire,
        }
        return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    def decode_access_token(self, token: str) -> Principal:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return Principal(
            user_id=str(payload["sub"]),
            organization_id=str(payload["organization_id"]),
            email=str(payload["email"]),
            roles=[Role(role) for role in payload.get("roles", [])],
        )
