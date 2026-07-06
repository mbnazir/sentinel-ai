from datetime import datetime, timezone
from uuid import uuid4


class CaseIdGenerator:
    def generate(self) -> str:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d")
        suffix = uuid4().hex[:8].upper()
        return f"SEN-{timestamp}-{suffix}"
