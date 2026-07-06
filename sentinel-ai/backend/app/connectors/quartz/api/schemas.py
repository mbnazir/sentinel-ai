from datetime import date

from pydantic import BaseModel


class QuartzSyncRequest(BaseModel):
    shift_date_from: date
    shift_date_to: date


class QuartzSyncResponse(BaseModel):
    session_count: int
    activity_count: int
