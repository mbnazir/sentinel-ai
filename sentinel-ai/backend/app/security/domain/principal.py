from dataclasses import dataclass

from app.security.domain.roles import Role


@dataclass(frozen=True)
class Principal:
    user_id: str
    organization_id: str
    email: str
    roles: list[Role]
