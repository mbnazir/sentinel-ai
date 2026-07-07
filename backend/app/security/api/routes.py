from fastapi import APIRouter

from app.security.domain.principal import Principal
from app.security.domain.roles import Role
from app.security.services.token_service import TokenService
from app.shared.api_response import ApiResponse

router = APIRouter()


@router.post("/dev-token", response_model=ApiResponse[dict[str, str]])
def create_dev_token() -> ApiResponse[dict[str, str]]:
    """Development-only token endpoint.

    Production must replace this with real user authentication / SSO.
    """
    principal = Principal(
        user_id="dev-admin",
        organization_id="ORG-DEV",
        email="admin@sentinel.local",
        roles=[Role.ADMIN],
    )
    return ApiResponse(data={"access_token": TokenService().create_access_token(principal), "token_type": "bearer"})
