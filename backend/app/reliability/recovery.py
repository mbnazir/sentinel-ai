from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.models import ScanChunkModel

async def stale_running_chunks(db:AsyncSession, older_than_minutes:int=30):
    cutoff=datetime.now(timezone.utc)-timedelta(minutes=older_than_minutes)
    result=await db.execute(select(ScanChunkModel).where(
        ScanChunkModel.status=="running",
        ScanChunkModel.started_at.is_not(None),
        ScanChunkModel.started_at<cutoff,
    ))
    return list(result.scalars())

def should_dead_letter(attempt:int,max_attempts:int=4)->bool:
    return attempt>=max_attempts
