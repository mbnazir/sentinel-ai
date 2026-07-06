from pydantic import BaseModel


class ImportSummary(BaseModel):
    connector_id: int
    connector_run_id: int | None = None
    sessions_imported: int = 0
    activities_imported: int = 0
    sessions_skipped: int = 0
    activities_skipped: int = 0
