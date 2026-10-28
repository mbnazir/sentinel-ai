from datetime import date
from enum import StrEnum
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

class ChunkStatus(StrEnum):
    PENDING="pending"; RUNNING="running"; COMPLETED="completed"; FAILED="failed"; CANCELLED="cancelled"

class ScanChunk(BaseModel):
    model_config=ConfigDict(frozen=True)
    scan_id:UUID
    chunk_index:int=Field(ge=0)
    date_from:date
    date_to:date
    agent_ids:tuple[str,...]=()
    status:ChunkStatus=ChunkStatus.PENDING
    attempt:int=0

class ScanProgress(BaseModel):
    total_chunks:int
    completed_chunks:int
    failed_chunks:int
    cancelled_chunks:int
    percent_complete:float=Field(ge=0,le=100)
