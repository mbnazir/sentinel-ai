from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict

class InvestigatorSummary(BaseModel):
    model_config=ConfigDict(frozen=True, from_attributes=True)
    case_id:UUID
    provider:str
    model:str
    prompt_version:str
    input_hash:str
    narrative:str
    created_at:datetime|None=None
