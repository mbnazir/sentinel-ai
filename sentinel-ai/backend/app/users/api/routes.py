from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database.session import get_db_session
from app.infrastructure.persistence.repositories.user_repository import UserRepository
from app.security.domain.principal import Principal
from app.security.domain.roles import Permission, Role
from app.security.services.token_service import TokenService
from app.security.api.dependencies import require_permission
from app.shared.api_response import ApiResponse
from app.users.api.schemas import CreateUserRequest, LoginRequest, TokenResponse, UserResponse
from app.users.services.user_service import UserService

router = APIRouter()


def to_response(user) -> UserResponse:
    return UserResponse(
        user_id=user.user_id,
        organization_id=user.organization_id,
        email=user.email,
        full_name=user.full_name,
        roles=[role.value for role in user.roles],
        is_active=user.is_active,
    )


@router.post("", response_model=ApiResponse[UserResponse])
def create_user(
    request: CreateUserRequest,
    _principal: Principal = Depends(require_permission(Permission.MANAGE_USERS)),
    session: Session = Depends(get_db_session),
) -> ApiResponse[UserResponse]:
    try:
        user = UserService(UserRepository(session)).create_local_user(
            organization_id=request.organization_id,
            email=request.email,
            full_name=request.full_name,
            password=request.password,
            roles=[Role(role) for role in request.roles],
        )
        return ApiResponse(data=to_response(user))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/login", response_model=ApiResponse[TokenResponse])
def login(
    request: LoginRequest,
    session: Session = Depends(get_db_session),
) -> ApiResponse[TokenResponse]:
    try:
        user = UserService(UserRepository(session)).authenticate_local_user(request.email, request.password)
        token = TokenService().create_access_token(
            Principal(
                user_id=user.user_id,
                organization_id=user.organization_id,
                email=user.email,
                roles=user.roles,
            )
        )
        return ApiResponse(data=TokenResponse(access_token=token))
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
