from datetime import datetime, timezone
from uuid import uuid4

from app.infrastructure.persistence.models_users import SentinelUserModel
from app.infrastructure.persistence.repositories.user_repository import UserRepository
from app.security.domain.principal import Principal
from app.security.services.token_service import TokenService
from app.sso.domain.sso_profile import SSOProfile
from app.sso.services.sso_role_mapper import SSORoleMapper


class SSOAuthService:
    def __init__(
        self,
        user_repository: UserRepository,
        role_mapper: SSORoleMapper | None = None,
        token_service: TokenService | None = None,
    ) -> None:
        self.user_repository = user_repository
        self.role_mapper = role_mapper or SSORoleMapper()
        self.token_service = token_service or TokenService()

    def upsert_sso_user_and_issue_token(self, profile: SSOProfile) -> str:
        model = self.user_repository.get_model_by_email(profile.email)
        roles = self.role_mapper.map_groups_to_roles(profile.groups)

        if model is None:
            model = SentinelUserModel(
                user_id=f"USR-{uuid4().hex[:12]}",
                organization_id=profile.organization_id,
                email=profile.email.lower(),
                full_name=profile.full_name,
                hashed_password=None,
                roles=[role.value for role in roles],
                is_active=True,
                auth_provider=profile.provider,
                external_subject=profile.subject,
                created_at=datetime.now(timezone.utc),
            )
        else:
            model.full_name = profile.full_name
            model.roles = [role.value for role in roles]
            model.auth_provider = profile.provider
            model.external_subject = profile.subject
            model.updated_at = datetime.now(timezone.utc)

        saved = self.user_repository.save_model(model)
        principal = Principal(
            user_id=saved.user_id,
            organization_id=saved.organization_id,
            email=saved.email,
            roles=roles,
        )
        return self.token_service.create_access_token(principal)
