from datetime import date
from typing import Any

import httpx

from app.connectors.quartz.config import QuartzConnectorConfig


class QuartzRestClient:
    def __init__(self, config: QuartzConnectorConfig) -> None:
        self.config = config

    def _headers(self) -> dict[str, str]:
        if not self.config.api_key:
            return {}
        return {"Authorization": f"Bearer {self.config.api_key}"}

    async def get_sessions(self, shift_date_from: date, shift_date_to: date) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
            response = await client.get(
                f"{self.config.base_url.rstrip('/')}/login-sessions",
                params={
                    "shift_date_from": shift_date_from.isoformat(),
                    "shift_date_to": shift_date_to.isoformat(),
                },
                headers=self._headers(),
            )
            response.raise_for_status()
            payload = response.json()
            return payload.get("data", payload)

    async def get_activities(self, login_session_ids: list[str]) -> list[dict[str, Any]]:
        if not login_session_ids:
            return []
        async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
            response = await client.post(
                f"{self.config.base_url.rstrip('/')}/activities/by-login-sessions",
                json={"login_session_ids": login_session_ids},
                headers=self._headers(),
            )
            response.raise_for_status()
            payload = response.json()
            return payload.get("data", payload)
