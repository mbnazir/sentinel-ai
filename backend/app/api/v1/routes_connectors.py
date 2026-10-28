from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.connector_factory import UnsupportedConnectorError, build_connector
from app.connectors.quartz import QuartzRestConnector
from app.core.database import get_db
from app.infrastructure.models import ConnectorModel

router = APIRouter(prefix="/connectors", tags=["connectors"])


class ConnectorCreate(BaseModel):
    name: str
    connector_type: str
    mode: str
    enabled: bool = True
    base_url: str | None = None
    config: dict[str, object] = Field(default_factory=dict)


class ConnectorRead(BaseModel):
    id: UUID
    name: str
    connector_type: str
    mode: str
    enabled: bool
    base_url: str | None
    config: dict[str, object]


@router.get("", response_model=list[ConnectorRead])
async def list_connectors(db: AsyncSession = Depends(get_db)) -> list[ConnectorRead]:
    result = await db.execute(
        select(ConnectorModel).order_by(ConnectorModel.created_at.desc()).limit(100)
    )
    return [_to_read(row) for row in result.scalars()]


@router.post("", response_model=ConnectorRead, status_code=status.HTTP_201_CREATED)
async def create_connector(
    payload: ConnectorCreate, db: AsyncSession = Depends(get_db)
) -> ConnectorRead:
    if not payload.name.strip():
        raise HTTPException(status_code=400, detail="Connector name is required")
    if payload.connector_type == "quartz" and payload.mode == "rest-api" and not payload.base_url:
        raise HTTPException(status_code=400, detail="Quartz REST connector requires base_url")
    row = ConnectorModel(
        name=payload.name.strip(),
        connector_type=payload.connector_type,
        mode=payload.mode,
        enabled=payload.enabled,
        base_url=payload.base_url,
        config_json=payload.config,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return _to_read(row)


@router.post("/{connector_id}/test")
async def test_connector(
    connector_id: UUID, db: AsyncSession = Depends(get_db)
) -> dict[str, object]:
    row = await db.get(ConnectorModel, connector_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Connector not found")
    try:
        connector = build_connector(row)
    except UnsupportedConnectorError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    try:
        connected = await connector.test_connection()
        return {"connected": connected}
    finally:
        if isinstance(connector, QuartzRestConnector):
            await connector.close()


def _to_read(row: ConnectorModel) -> ConnectorRead:
    return ConnectorRead(
        id=row.id,
        name=row.name,
        connector_type=row.connector_type,
        mode=row.mode,
        enabled=row.enabled,
        base_url=row.base_url,
        config=row.config_json,
    )
