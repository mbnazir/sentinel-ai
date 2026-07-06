from datetime import date

from pydantic import BaseModel, Field, model_validator


class ConnectorSyncRequest(BaseModel):
    shift_date_from: date = Field(..., description="Inclusive shift date start.")
    shift_date_to: date = Field(..., description="Inclusive shift date end.")

    @model_validator(mode="after")
    def validate_date_range(self) -> "ConnectorSyncRequest":
        if self.shift_date_to < self.shift_date_from:
            raise ValueError("shift_date_to must be greater than or equal to shift_date_from")
        return self
