from sqlalchemy.orm import Session

from app.infrastructure.persistence.models_users import SentinelUserModel
from app.security.domain.roles import Role
from app.users.domain.user import User


class UserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_email(self, email: str) -> User | None:
        model = self.session.query(SentinelUserModel).filter_by(email=email.lower()).one_or_none()
        return self._to_domain(model) if model else None

    def get_model_by_email(self, email: str) -> SentinelUserModel | None:
        return self.session.query(SentinelUserModel).filter_by(email=email.lower()).one_or_none()

    def save_model(self, model: SentinelUserModel) -> SentinelUserModel:
        self.session.add(model)
        self.session.commit()
        self.session.refresh(model)
        return model

    def list_by_organization(self, organization_id: str) -> list[User]:
        models = self.session.query(SentinelUserModel).filter_by(organization_id=organization_id).all()
        return [self._to_domain(model) for model in models]

    def _to_domain(self, model: SentinelUserModel) -> User:
        return User(
            user_id=model.user_id,
            organization_id=model.organization_id,
            email=model.email,
            full_name=model.full_name,
            roles=[Role(role) for role in model.roles],
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
