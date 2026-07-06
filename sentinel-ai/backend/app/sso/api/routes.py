from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database.session import get_db_session
from app.infrastructure.persistence.repositories.user_repository import UserRepository
from app.shared.api_response import ApiResponse
from app.sso.api.schemas import SSOCallbackRequest, SSOLoginResponse
from app.sso.providers.mock_provider import MockSSOProvider
from app.sso.services.sso_auth_service import SSOAuthService

router = APIRouter()


@router.post("/mock/callback", response_model=ApiResponse[SSOLoginResponse])
async def mock_sso_callback(
    request: SSOCallbackRequest,
    session: Session = Depends(get_db_session),
) -> ApiResponse[SSOLoginResponse]:
    provider = MockSSOProvider()
    profile = await provider.exchange_code(request.code, request.redirect_uri)
    token = SSOAuthService(UserRepository(session)).upsert_sso_user_and_issue_token(profile)
    return ApiResponse(
        data=SSOLoginResponse(
            access_token=token,
            provider=provider.provider_name,
        )
    )
