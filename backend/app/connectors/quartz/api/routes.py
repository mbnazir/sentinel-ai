from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.connectors.quartz.api.schemas import QuartzSyncRequest, QuartzSyncResponse
from app.connectors.quartz.client.quartz_api_client import QuartzAPIClient
from app.connectors.quartz.client.quartz_api_models import QuartzAPIConfig
from app.connectors.quartz.persistence.normalized_ingestion_repository import NormalizedIngestionRepository
from app.connectors.quartz.services.quartz_ingestion_service import QuartzIngestionService
from app.connectors.quartz.services.quartz_persisted_ingestion_service import QuartzPersistedIngestionService
from app.core.database.session import get_db_session
from app.shared.api_response import ApiResponse
import os

router = APIRouter()


def build_ingestion_service(session: Session) -> QuartzPersistedIngestionService:
    config = QuartzAPIConfig(
        base_url=os.getenv("QUARTZ_API_BASE_URL", "http://localhost:8080"),
        api_key=os.getenv("QUARTZ_API_KEY", ""),
        page_size=int(os.getenv("QUARTZ_API_PAGE_SIZE", "500")),
        max_retries=int(os.getenv("QUARTZ_API_MAX_RETRIES", "3")),
    )
    return QuartzPersistedIngestionService(
        ingestion_service=QuartzIngestionService(QuartzAPIClient(config)),
        repository=NormalizedIngestionRepository(session),
    )


@router.post("/sync", response_model=ApiResponse[QuartzSyncResponse])
async def sync_quartz_shift_range(
    request: QuartzSyncRequest,
    session: Session = Depends(get_db_session),
) -> ApiResponse[QuartzSyncResponse]:
    result = await build_ingestion_service(session).ingest_and_persist(
        organization_id=request.organization_id,
        shift_date_from=request.shift_date_from,
        shift_date_to=request.shift_date_to,
    )
    return ApiResponse(
        data=QuartzSyncResponse(
            fetched_sessions=result.fetched_sessions,
            fetched_activities=result.fetched_activities,
            persisted_sessions=result.persisted_sessions,
            persisted_activities=result.persisted_activities,
        )
    )
