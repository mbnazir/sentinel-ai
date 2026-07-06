from fastapi import APIRouter

from app.connectors.quartz.api.schemas import QuartzSyncRequest, QuartzSyncResponse
from app.connectors.quartz.connector import QuartzConnector
from app.shared.api_response import ApiResponse

router = APIRouter()


@router.post("/sync", response_model=ApiResponse[QuartzSyncResponse])
async def sync_quartz_shift_range(request: QuartzSyncRequest) -> ApiResponse[QuartzSyncResponse]:
    connector = QuartzConnector()
    result = await connector.ingestion_service.ingest_shift_date_range(
        request.shift_date_from,
        request.shift_date_to,
    )
    return ApiResponse(
        data=QuartzSyncResponse(
            session_count=result.session_count,
            activity_count=result.activity_count,
        )
    )
