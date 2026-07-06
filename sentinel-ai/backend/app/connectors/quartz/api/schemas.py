from datetime import date

from pydantic import BaseModel


class QuartzSyncRequest(BaseModel):
    organization_id: str
    shift_date_from: date
    shift_date_to: date


class QuartzSyncResponse(BaseModel):
    fetched_sessions: int
    fetched_activities: int
    persisted_sessions: int
    persisted_activities: int
