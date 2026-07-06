from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.connectors.schemas import ConnectorSyncRequest
from app.application.dto.import_summary import ImportSummary
from app.application.services.connector_factory import ConnectorFactory
from app.application.services.connector_sync_service import ConnectorSyncService
from app.core.database.session import get_db_session
from app.core.exceptions.exceptions import NotFoundError
from app.infrastructure.persistence.models import ConnectorModel
from app.shared.api_response import ApiResponse

router = APIRouter()


@router.get("", response_model=ApiResponse[list[dict[str, str]]])
def list_connectors_placeholder() -> ApiResponse[list[dict[str, str]]]:
    return ApiResponse(data=[], message="Connector list endpoint scaffold. Repository query comes next.")


@router.post("/{connector_id}/sync", response_model=ApiResponse[ImportSummary])
async def sync_connector(
    connector_id: int,
    request: ConnectorSyncRequest,
    db: Session = Depends(get_db_session),
) -> ApiResponse[ImportSummary]:
    connector_model = db.execute(
        select(ConnectorModel).where(ConnectorModel.id == connector_id)
    ).scalar_one_or_none()
    if connector_model is None:
        raise NotFoundError(f"Connector {connector_id} not found.")

    connector = ConnectorFactory().create(
        connector_type=connector_model.connector_type,
        configuration=connector_model.configuration,
    )
    service = ConnectorSyncService(
        db=db,
        connector=connector,
        organization_id=connector_model.organization_id,
        connector_id=connector_model.id,
        connector_run_id=None,
    )
    summary = await service.synchronize_shift_dates(
        shift_date_from=request.shift_date_from,
        shift_date_to=request.shift_date_to,
    )
    return ApiResponse(data=summary, message="Connector synchronization completed.")
