from datetime import datetime, timezone
from uuid import uuid4

from app.infrastructure.persistence.models_users import SentinelUserModel
from app.infrastructure.persistence.repositories.user_repository import UserRepository
from app.security.domain.roles import Role
from app.security.services.password_service import PasswordService
from app.users.domain.user import User


class UserService:
    def __init__(
        self,
        repository: UserRepository,
        password_service: PasswordService | None = None,
    ) -> None:
        self.repository = repository
        self.password_service = password_service or PasswordService()

    def create_local_user(
        self,
        organization_id: str,
        email: str,
        full_name: str,
        password: str,
        roles: list[Role],
    ) -> User:
        existing = self.repository.get_by_email(email)
        if existing:
            raise ValueError("User already exists.")

        model = SentinelUserModel(
            user_id=f"USR-{uuid4().hex[:12]}",
            organization_id=organization_id,
            email=email.lower(),
            full_name=full_name,
            hashed_password=self.password_service.hash_password(password),
            roles=[role.value for role in roles],
            is_active=True,
            auth_provider="local",
            created_at=datetime.now(timezone.utc),
        )
        saved = self.repository.save_model(model)
        return self.repository._to_domain(saved)

    def authenticate_local_user(self, email: str, password: str) -> User:
        model = self.repository.get_model_by_email(email)
        if model is None or not model.hashed_password or not model.is_active:
            raise ValueError("Invalid credentials.")

        if not self.password_service.verify_password(password, model.hashed_password):
            raise ValueError("Invalid credentials.")

        return self.repository._to_domain(model)
