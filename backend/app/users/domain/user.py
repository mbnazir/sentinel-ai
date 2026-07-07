from dataclasses import dataclass
from datetime import datetime

from app.security.domain.roles import Role


@dataclass(frozen=True)
class User:
    user_id: str
    organization_id: str
    email: str
    full_name: str
    roles: list[Role]
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None
