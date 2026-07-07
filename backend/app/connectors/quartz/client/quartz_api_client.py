from datetime import date
from typing import Any

import httpx

from app.connectors.quartz.client.quartz_api_models import QuartzAPIConfig, QuartzPage


class QuartzAPIClient:
    """Production-shaped Quartz REST client.

    Expected Quartz API contract:
    - GET /api/sessions?shift_date_from=YYYY-MM-DD&shift_date_to=YYYY-MM-DD&page_size=N&cursor=X
    - POST /api/activities/batch with {"login_session_ids": [...]}

    Actual endpoint paths can be adapted in this single class without changing the connector core.
    """

    def __init__(self, config: QuartzAPIConfig) -> None:
        self.config = config

    async def fetch_sessions_page(
        self,
        shift_date_from: date,
        shift_date_to: date,
        cursor: str | None = None,
    ) -> QuartzPage:
        params = {
            "shift_date_from": shift_date_from.isoformat(),
            "shift_date_to": shift_date_to.isoformat(),
            "page_size": self.config.page_size,
        }
        if cursor:
            params["cursor"] = cursor

        payload = await self._request("GET", "/api/sessions", params=params)
        return QuartzPage(items=list(payload.get("items", [])), next_cursor=payload.get("next_cursor"))

    async def fetch_activities_batch(self, login_session_ids: list[str]) -> list[dict[str, Any]]:
        if not login_session_ids:
            return []
        payload = await self._request(
            "POST",
            "/api/activities/batch",
            json={"login_session_ids": login_session_ids},
        )
        return list(payload.get("items", []))

    async def _request(self, method: str, path: str, **kwargs) -> dict[str, Any]:
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self.config.api_key}"
        headers["Accept"] = "application/json"

        last_error: Exception | None = None

        for attempt in range(1, self.config.max_retries + 1):
            try:
                async with httpx.AsyncClient(
                    base_url=self.config.base_url,
                    timeout=self.config.timeout_seconds,
                ) as client:
                    response = await client.request(method, path, headers=headers, **kwargs)
                    response.raise_for_status()
                    return dict(response.json())
            except Exception as exc:
                last_error = exc
                if attempt >= self.config.max_retries:
                    break

        raise RuntimeError(f"Quartz API request failed after {self.config.max_retries} attempts.") from last_error
