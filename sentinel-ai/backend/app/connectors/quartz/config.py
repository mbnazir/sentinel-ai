from pydantic import BaseModel, Field


class QuartzConnectorConfig(BaseModel):
    base_url: str = Field(..., description="Quartz API base URL.")
    api_key: str | None = Field(default=None, description="Optional API key.")
    timeout_seconds: int = 60
