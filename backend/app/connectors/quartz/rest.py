from __future__ import annotations
from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass
from datetime import date, datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Generic, TypeVar
import random
import time
import structlog
import httpx
import asyncio
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter
from app.application.normalized import (
    NormalizedActivity,
    NormalizedLoginSession,
)
# ---------------------------------------------------------------------------
# Quartz connector configuration
# ---------------------------------------------------------------------------
class QuartzConnectorError(RuntimeError):
    """
    Raised when communication with the Quartz REST API fails or Quartz
    returns an invalid response.
    """
    def __init__(self, message: str, *, failure_category: str = "connector_error",
                 http_status: int | None = None, attempts: int = 1) -> None:
        super().__init__(message)
        self.failure_category = failure_category
        self.http_status = http_status
        self.attempts = attempts


T = TypeVar("T")


@dataclass(frozen=True)
class QuartzPageResult(Generic[T]):
    items: list[T]
    next_cursor: str | None
    expected_count: int | None
    attempts: int
    latency_ms: float
class QuartzConnectorConfig(BaseModel):
    """
    Configuration used by QuartzRestConnector.
    extra="ignore" is intentional so older/newer Sentinel connector records
    can contain additional configuration without breaking this connector.
    """
    model_config = ConfigDict(extra="ignore")
    base_url: str
    sessions_path: str = "/sentinel/LoginSessions"
    activities_path: str = "/sentinel/Activities"
    timeout_seconds: float = Field(
        default=30.0,
        gt=0,
    )
    activity_session_id_batch_size: int = Field(default=25, ge=1, le=100)
    request_max_attempts: int = Field(default=4, ge=1, le=10)
    retry_backoff_base_seconds: float = Field(default=0.5, ge=0, le=30)
    retry_backoff_max_seconds: float = Field(default=20.0, ge=0, le=120)
    bearer_token: str | None = Field(default=None, repr=False)
    page_size: int = Field(
        default=500,
        ge=1,
        le=5000,
    )
    verify_tls: bool = True
    headers: dict[str, str] = Field(
        default_factory=dict
    )
# ---------------------------------------------------------------------------
# Quartz REST connector
# ---------------------------------------------------------------------------
class QuartzRestConnector:
    """
    Read-only REST connector for Quartz.
    Responsibilities:
    - retrieve LoginSessions from Quartz
    - retrieve Activities from Quartz
    - support Quartz cursor pagination
    - normalize Quartz source records into Sentinel domain models
    - preserve Quartz-specific evidence in metadata
    - never modify Quartz data
    """
    def __init__(
        self,
        config: QuartzConnectorConfig | None = None,
        *,
        base_url: str | None = None,
        sessions_path: str | None = None,
        activities_path: str | None = None,
        timeout_seconds: float | None = None,
        activity_session_id_batch_size: int | None = None,
        request_max_attempts: int | None = None,
        retry_backoff_base_seconds: float | None = None,
        retry_backoff_max_seconds: float | None = None,
        bearer_token: str | None = None,
        page_size: int | None = None,
        verify_tls: bool | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        """
        Supports both:
            QuartzRestConnector(config)
        and:
            QuartzRestConnector(
                base_url="https://...",
                sessions_path="/sentinel/LoginSessions",
                ...
            )
        """
        if config is None:
            if not base_url:
                raise ValueError(
                    "QuartzRestConnector requires either "
                    "QuartzConnectorConfig or base_url"
                )
            config = QuartzConnectorConfig(
                base_url=base_url,
                sessions_path=(
                    sessions_path
                    if sessions_path is not None
                    else "/sentinel/LoginSessions"
                ),
                activities_path=(
                    activities_path
                    if activities_path is not None
                    else "/sentinel/Activities"
                ),
                timeout_seconds=(
                    timeout_seconds
                    if timeout_seconds is not None
                    else 30.0
                ),
                activity_session_id_batch_size=(activity_session_id_batch_size
                    if activity_session_id_batch_size is not None else 25),
                request_max_attempts=request_max_attempts if request_max_attempts is not None else 4,
                retry_backoff_base_seconds=(retry_backoff_base_seconds
                                            if retry_backoff_base_seconds is not None else 0.5),
                retry_backoff_max_seconds=(retry_backoff_max_seconds
                                           if retry_backoff_max_seconds is not None else 20.0),
                bearer_token=bearer_token,
                page_size=(
                    page_size
                    if page_size is not None
                    else 500
                ),
                verify_tls=(
                    verify_tls
                    if verify_tls is not None
                    else True
                ),
                headers=headers or {},
            )
        self.config = config
        self.base_url = config.base_url.rstrip("/")
        self.sessions_path = _normalize_path(config.sessions_path)
        self.activities_path = _normalize_path(config.activities_path)
        self.timeout_seconds = config.timeout_seconds
        self.page_size = config.page_size
        self.activity_session_id_batch_size = config.activity_session_id_batch_size
        self.request_max_attempts = config.request_max_attempts
        self.retry_backoff_base_seconds = config.retry_backoff_base_seconds
        self.retry_backoff_max_seconds = config.retry_backoff_max_seconds
        self.verify_tls = config.verify_tls
        self.headers = dict(config.headers)
        if config.bearer_token:
            self.headers.setdefault("Authorization", f"Bearer {config.bearer_token}")
    async def close(self) -> None:
        """
        Close connector resources.
        QuartzRestConnector currently creates short-lived AsyncClient
        instances using async context managers, so there is no persistent
        HTTP client to close. This method exists to satisfy the connector
        lifecycle contract expected by Sentinel.
        """
        return None
    # ------------------------------------------------------------------
    # Connectivity
    # ------------------------------------------------------------------
    async def test_connection(self) -> bool:
        """
        Perform a lightweight Quartz REST connectivity test.
        Returning False rather than raising is useful for the Sentinel
        connector-test endpoint.
        """
        today = date.today()
        params = {
            "shift_date_from": today.isoformat(),
            "shift_date_to": today.isoformat(),
            "limit": 1,
        }
        try:
            async with self._client() as client:
                response = await client.get(
                    self.sessions_path,
                    params=params,
                )
                response.raise_for_status()
                payload = response.json()
                return (
                    isinstance(payload, dict)
                    and isinstance(payload.get("items"), list)
                )
        except Exception:
            return False
    # ------------------------------------------------------------------
    # Sessions
    # ------------------------------------------------------------------
    async def iter_sessions(
        self,
        *,
        shift_date_from: date,
        shift_date_to: date,
    ) -> AsyncIterator[NormalizedLoginSession]:
        """
        Stream Quartz LoginSessions using cursor pagination.
        Request dates are ISO YYYY-MM-DD.
        Quartz may return shift_date as MM/DD/YYYY, which is normalized
        separately without deriving it from start_date.
        """
        cursor: str | None = None
        seen_cursors: set[str] = set()
        page_number = 0
        while True:
            page = await self.fetch_sessions_page(shift_date_from=shift_date_from,
                shift_date_to=shift_date_to, cursor=cursor, context={"page_number": page_number + 1})
            for item in page.items:
                yield item
            cursor = page.next_cursor
            page_number += 1
            if cursor is None:
                break
            if cursor in seen_cursors:
                raise QuartzConnectorError("Quartz LoginSessions returned a repeated pagination cursor",
                                           failure_category="pagination_cursor_repeated")
            seen_cursors.add(cursor)

    async def fetch_sessions_page(self, *, shift_date_from: date, shift_date_to: date,
                                  cursor: str | None = None,
                                  context: dict[str, object] | None = None
                                  ) -> QuartzPageResult[NormalizedLoginSession]:
        params: dict[str, Any] = {"shift_date_from": shift_date_from.isoformat(),
            "shift_date_to": shift_date_to.isoformat(), "limit": self.page_size}
        if cursor is not None:
            params["cursor"] = cursor
        payload, attempts, latency_ms = await self._get_json_with_metadata(
            self.sessions_path, params, operation="Quartz LoginSessions", context=context)
        items = [self._normalize_session(item) for item in _response_items(payload, "Quartz LoginSessions")]
        return QuartzPageResult(items, _next_cursor(payload), _expected_count(payload), attempts, latency_ms)
    # ------------------------------------------------------------------
    # Activities
    # ------------------------------------------------------------------
    async def iter_activities(
        self,
        *,
        login_session_ids: list[str],
    ) -> AsyncIterator[NormalizedActivity]:
        """
        Stream Quartz Activities for supplied login session IDs.
        Login session IDs are sent in groups to prevent excessively large
        URLs. Each group independently uses cursor pagination.
        """
        if not login_session_ids:
            return
        for session_ids in _chunks(login_session_ids, self.activity_session_id_batch_size):
            cursor: str | None = None
            seen_cursors: set[str] = set()
            page_number = 0
            while True:
                page = await self.fetch_activities_page(login_session_ids=session_ids, cursor=cursor,
                    context={"page_number": page_number + 1})
                for item in page.items:
                    yield item
                cursor = page.next_cursor
                page_number += 1
                if cursor is None:
                    break
                if cursor in seen_cursors:
                    raise QuartzConnectorError("Quartz Activities returned a repeated pagination cursor",
                                               failure_category="pagination_cursor_repeated")
                seen_cursors.add(cursor)

    async def fetch_activities_page(self, *, login_session_ids: list[str], cursor: str | None = None,
                                    context: dict[str, object] | None = None
                                    ) -> QuartzPageResult[NormalizedActivity]:
        if not login_session_ids:
            raise ValueError("at least one login session ID is required")
        if len(login_session_ids) > self.activity_session_id_batch_size:
            raise ValueError("activity page exceeds configured session ID batch size")
        params: dict[str, Any] = {"login_session_ids": ",".join(login_session_ids),
                                  "limit": self.page_size}
        if cursor is not None:
            params["cursor"] = cursor
        payload, attempts, latency_ms = await self._get_json_with_metadata(
            self.activities_path, params, operation="Quartz Activities", context=context)
        items = [self._normalize_activity(item) for item in _response_items(payload, "Quartz Activities")]
        return QuartzPageResult(items, _next_cursor(payload), _expected_count(payload), attempts, latency_ms)
    # ------------------------------------------------------------------
    # HTTP
    # ------------------------------------------------------------------
    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(
                connect=10.0,
                read=self.timeout_seconds,
                write=15.0,
                pool=10.0,
            ),
            verify=self.verify_tls,
            headers=self.headers,
            follow_redirects=True,
            trust_env=False,
        )
    async def _get_json(
        self,
        client: httpx.AsyncClient,
        url: str,
        params: dict[str, object],
        operation: str,
    ) -> dict:
        payload, _, _ = await self._request_json(client, url, params, operation, context=None)
        return payload

    async def _get_json_with_metadata(self, url: str, params: dict[str, object], *, operation: str,
                                     context: dict[str, object] | None = None
                                     ) -> tuple[dict[str, Any], int, float]:
        async with self._client() as client:
            payload, attempts, latency = await self._request_json(client, url, params, operation, context)
        return payload, attempts, latency

    async def _request_json(self, client: httpx.AsyncClient, url: str, params: dict[str, object],
                            operation: str, context: dict[str, object] | None
                            ) -> tuple[dict[str, Any], int, float]:
        logger = structlog.get_logger(__name__)
        started = time.monotonic()
        for attempt in range(1, self.request_max_attempts + 1):
            try:
                response = await client.get(url, params=params)
                if response.status_code in {429, 502, 503, 504}:
                    response.raise_for_status()
                response.raise_for_status()
                try:
                    payload = response.json()
                except (ValueError, TypeError) as exc:
                    raise QuartzConnectorError(f"{operation} returned malformed JSON",
                        failure_category="malformed_response") from exc
                if not isinstance(payload, dict):
                    raise QuartzConnectorError(f"{operation} returned a non-object JSON payload",
                        failure_category="malformed_response")
                latency = (time.monotonic() - started) * 1000
                safe_context = context or {}
                logger.info("quartz_page_fetched", operation=operation, **safe_context,
                            request_latency_ms=round(latency, 2), retry_count=attempt - 1,
                            item_count=len(payload.get("items", [])) if isinstance(payload.get("items", []), list) else None)
                return payload, attempt, latency
            except httpx.HTTPStatusError as exc:
                status_code = exc.response.status_code
                retryable = status_code in {429, 502, 503, 504}
                category = f"http_{status_code}"
                if not retryable or attempt >= self.request_max_attempts:
                    raise QuartzConnectorError(f"{operation} returned HTTP {status_code}",
                        failure_category=category, http_status=status_code, attempts=attempt) from exc
                delay = _retry_delay(attempt, self.retry_backoff_base_seconds,
                    self.retry_backoff_max_seconds, exc.response.headers.get("Retry-After"))
                logger.warning("quartz_request_retry", operation=operation, **(context or {}),
                               failure_category=category, retry_count=attempt, retry_delay_seconds=delay)
                await asyncio.sleep(delay)
            except (httpx.ConnectTimeout, httpx.PoolTimeout) as exc:
                category = "connection_timeout"
                if attempt >= self.request_max_attempts:
                    raise QuartzConnectorError(f"{operation} failed after {attempt} attempts (connection timeout)",
                        failure_category=category, attempts=attempt) from exc
                delay = _retry_delay(attempt, self.retry_backoff_base_seconds, self.retry_backoff_max_seconds)
                logger.warning("quartz_request_retry", operation=operation, **(context or {}),
                               failure_category=category, retry_count=attempt, retry_delay_seconds=delay)
                await asyncio.sleep(delay)
            except httpx.ReadTimeout as exc:
                category = "read_timeout"
                if attempt >= self.request_max_attempts:
                    raise QuartzConnectorError(f"{operation} failed after {attempt} attempts (read timeout)",
                        failure_category=category, attempts=attempt) from exc
                delay = _retry_delay(attempt, self.retry_backoff_base_seconds, self.retry_backoff_max_seconds)
                logger.warning("quartz_request_retry", operation=operation, **(context or {}),
                               failure_category=category, retry_count=attempt, retry_delay_seconds=delay)
                await asyncio.sleep(delay)
            except httpx.ConnectError as exc:
                category = "connection_error"
                if attempt >= self.request_max_attempts:
                    raise QuartzConnectorError(f"{operation} failed after {attempt} attempts (connection error)",
                        failure_category=category, attempts=attempt) from exc
                delay = _retry_delay(attempt, self.retry_backoff_base_seconds, self.retry_backoff_max_seconds)
                logger.warning("quartz_request_retry", operation=operation, **(context or {}),
                               failure_category=category, retry_count=attempt, retry_delay_seconds=delay)
                await asyncio.sleep(delay)
        raise AssertionError("retry loop exited unexpectedly")
    # ------------------------------------------------------------------
    # Normalization: LoginSessions
    # ------------------------------------------------------------------
    def _normalize_session(
        self,
        row: dict[str, Any],
    ) -> NormalizedLoginSession:
        get = row.get
        metadata: dict[str, object] = _without_none(
            {
                # Quartz source/session evidence not currently represented
                # as first-class fields on NormalizedLoginSession.
                "data_source_id": get("data_source_id"),
                "session_source": get("session_source"),
                "resolve_dispute_by": get("resolve_dispute_by"),
                "closed_by": get("closed_by"),
                "closed_by_type": get("closed_by_type"),
                "overtime": get("overtime"),
                "regular_hour": get("regular_hour"),
            }
        )
        return NormalizedLoginSession(
            source_system="quartz",
            source_session_id=_required_str(
                get("id"),
                "id",
            ),
            agent_id=_required_str(
                get("agent_id"),
                "agent_id",
            ),
            supervisor_id=_optional_str(
                get("supervisor_id")
            ),
            manager_id=_optional_str(
                get("manager_id")
            ),
            site_id=_optional_str(
                get("site_id")
            ),
            site_name=_optional_str(
                get("site_name")
            ),
            team_id=_optional_str(
                get("team_id")
            ),
            # IMPORTANT:
            # Quartz shift_date is the authoritative business shift date.
            # Do not infer it from start_date.
            shift_date=_date(
                get("shift_date")
            ),
            start_at=_datetime(
                get("start_date")
            ),
            end_at=_optional_datetime(
                get("end_date")
            ),
            status_id=_optional_int(
                get("status_id")
            ),
            dispute_reason_id=_optional_int(
                get("dispute_reason_id")
            ),
            dispute_state=_optional_int(
                get("dispute_state")
            ),
            supervisor_status_id=_optional_int(
                get("supervisor_status_id")
            ),
            ready_for_payroll=_bool(
                get("ready_for_payroll")
            ),
            payroll_adjusted=_bool(
                get("payroll_adjusted")
            ),
            payroll_adjusted_at=_optional_datetime(
                get("payroll_adjust_dt")
            ),
            session_added_by=_optional_str(
                get("session_added_by")
            ),
            add_session_reason_id=_optional_int(
                get("add_session_reason_id")
            ),
            agent_action_at=_optional_datetime(
                get("agent_action_timestamp")
            ),
            supervisor_action_at=_optional_datetime(
                get("supervisor_action_timestamp")
            ),
            manager_action_at=_optional_datetime(
                get("manager_action_timestamp")
            ),
            multiple_logins=(
                _optional_int(
                    get("multiple_logins")
                )
                or 0
            ),
            agent_ip=_optional_str(
                get("agent_ip")
            ),
            machine_hostname=_optional_str(
                get("machine_hostname")
            ),
            primary_campaign_id=_optional_str(
                get("primary_campaign_id")
            ),
            primary_campaign_name=_optional_str(
                get("primary_campaign_name")
            ),
            primary_client_id=_optional_int(
                get("primary_client_id")
            ),
            primary_client_name=_optional_str(
                get("primary_client_name")
            ),
            metadata=metadata,
        )
    # ------------------------------------------------------------------
    # Normalization: Activities
    # ------------------------------------------------------------------
    def _normalize_activity(
        self,
        row: dict[str, Any],
    ) -> NormalizedActivity:
        get = row.get
        start_at = _datetime(
            get("start_time")
        )
        end_at = _optional_datetime(
            get("end_time")
        )
        # Quartz returns a display value such as:
        #
        #     "0h 3m 32s"
        #
        # Do NOT pass this into int().
        #
        # Sentinel derives the analytical duration from timestamps and keeps
        # the original Quartz display value in metadata for evidence.
        duration_seconds: int | None = None
        if end_at is not None:
            calculated_duration = int(
                (end_at - start_at).total_seconds()
            )
            if calculated_duration < 0:
                raise QuartzConnectorError(
                    "Quartz activity has end_time before start_time: "
                    f"activity_id={get('id')}, "
                    f"start_time={get('start_time')}, "
                    f"end_time={get('end_time')}"
                )
            duration_seconds = calculated_duration
        metadata: dict[str, object] = _without_none(
            {
                "quartz_duration": get("duration"),
                "computer_merged": get("computer_merged"),
            }
        )
        data_source_id = _required_int(get("data_source_id"), "data_source_id")
        if data_source_id not in range(6):
            raise QuartzConnectorError(
                f"Unsupported Quartz data_source_id: {data_source_id} "
                f"(activity_id={get('id')})"
            )

        return NormalizedActivity(
            source_system="quartz",
            source_activity_id=_required_str(
                get("id"),
                "id",
            ),
            source_session_id=_required_str(
                get("login_session_id"),
                "login_session_id",
            ),
            agent_id=_optional_str(
                get("agent_id")
            ),
            data_source_id=data_source_id,
            activity_type_id=_required_int(
                get("activity_type_id"),
                "activity_type_id",
            ),
            source_id=_optional_int(
                get("source_id")
            ),
            start_at=start_at,
            end_at=end_at,
            duration_seconds=duration_seconds,
            inactivity_seconds=(
                _optional_int(
                    get("inactivity_time")
                )
                or 0
            ),
            campaign_id=_optional_str(
                get("campaign_id")
            ),
            campaign_name=_optional_str(
                get("campaign_name")
            ),
            client_id=_optional_int(
                get("client_id")
            ),
            comment=_optional_str(
                get("comment")
            ),
            created_at=_optional_datetime(
                get("created_at")
            ),
            updated_at=_optional_datetime(
                get("updated_at")
            ),
            metadata=metadata,
        )
# ---------------------------------------------------------------------------
# Response helpers
# ---------------------------------------------------------------------------
def _response_items(
    payload: dict[str, Any],
    operation: str,
) -> list[dict[str, Any]]:
    raw_items = payload.get("items", [])
    if raw_items is None:
        return []
    if not isinstance(raw_items, list):
        raise QuartzConnectorError(
            f"{operation} response field 'items' must be a list"
        )
    items: list[dict[str, Any]] = []
    for index, item in enumerate(raw_items):
        if not isinstance(item, dict):
            raise QuartzConnectorError(
                f"{operation} item at index {index} "
                "must be a JSON object"
            )
        items.append(item)
    return items
def _next_cursor(
    payload: dict[str, Any],
) -> str | None:
    value = payload.get("next_cursor")
    if value is None:
        return None
    value = str(value).strip()
    if not value:
        return None
    return value


def _expected_count(payload: dict[str, Any]) -> int | None:
    value = payload.get("expected_count")
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise QuartzConnectorError("Quartz response expected_count must be a non-negative integer",
                                   failure_category="malformed_response")
    return value


def _retry_delay(attempt: int, base: float, maximum: float,
                 retry_after: str | None = None) -> float:
    backoff = min(maximum, base * (2 ** (attempt - 1)))
    requested = _retry_after_seconds(retry_after)
    delay = min(maximum, max(backoff, requested or 0.0))
    return delay + random.uniform(0, min(0.25, max(0.01, delay * 0.1)))


def _retry_after_seconds(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return max(0.0, float(int(value.strip())))
    except (ValueError, TypeError):
        try:
            when = parsedate_to_datetime(value)
            if when.tzinfo is None:
                when = when.replace(tzinfo=timezone.utc)
            return max(0.0, (when - datetime.now(timezone.utc)).total_seconds())
        except (TypeError, ValueError, OverflowError):
            return None
# ---------------------------------------------------------------------------
# Date / datetime helpers
# ---------------------------------------------------------------------------
def _datetime(
    value: Any,
) -> datetime:
    """
    Parse required datetime.
    Quartz currently returns ISO-8601 timestamps such as:
        2026-08-25T02:03:08+00:00
    """
    if isinstance(value, datetime):
        return value
    if value is None:
        raise ValueError(
            "required datetime value is missing"
        )
    if isinstance(value, str):
        value = value.strip()
        if not value:
            raise ValueError(
                "required datetime value is empty"
            )
    return TypeAdapter(
        datetime
    ).validate_python(value)
def _optional_datetime(
    value: Any,
) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
    return _datetime(value)
def _date(
    value: Any,
) -> date:
    """
    Quartz request dates are ISO YYYY-MM-DD, but Quartz LoginSessions may
    return shift_date as MM/DD/YYYY.
    Both representations are accepted.
    """
    if isinstance(value, date) and not isinstance(
        value,
        datetime,
    ):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        value = value.strip()
        if not value:
            raise ValueError(
                "required date value is empty"
            )
        for fmt in (
            "%Y-%m-%d",
            "%m/%d/%Y",
        ):
            try:
                return datetime.strptime(
                    value,
                    fmt,
                ).date()
            except ValueError:
                continue
    return TypeAdapter(
        date
    ).validate_python(value)
# ---------------------------------------------------------------------------
# Primitive helpers
# ---------------------------------------------------------------------------
def _optional_int(
    value: Any,
) -> int | None:
    """
    Convert genuine integer Quartz fields.
    Do not use this function for Quartz's human-readable duration field.
    """
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
    return int(value)
def _required_int(
    value: Any,
    field_name: str,
) -> int:
    parsed = _optional_int(value)
    if parsed is None:
        raise ValueError(
            f"required integer field '{field_name}' is missing"
        )
    return parsed
def _optional_str(
    value: Any,
) -> str | None:
    if value is None:
        return None
    value = str(value).strip()
    if not value:
        return None
    return value
def _required_str(
    value: Any,
    field_name: str,
) -> str:
    parsed = _optional_str(value)
    if parsed is None:
        raise ValueError(
            f"required string field '{field_name}' is missing"
        )
    return parsed
def _bool(
    value: Any,
) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value != 0
    if isinstance(value, float):
        return value != 0
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {
            "1",
            "true",
            "yes",
            "y",
            "on",
        }:
            return True
        if normalized in {
            "0",
            "false",
            "no",
            "n",
            "off",
            "",
        }:
            return False
    return bool(value)
# ---------------------------------------------------------------------------
# Miscellaneous helpers
# ---------------------------------------------------------------------------
def _without_none(
    values: dict[str, object | None],
) -> dict[str, object]:
    return {
        key: value
        for key, value in values.items()
        if value is not None
    }
def _normalize_path(
    value: str,
) -> str:
    value = value.strip()
    if not value:
        raise ValueError(
            "Quartz endpoint path cannot be empty"
        )
    if not value.startswith("/"):
        value = "/" + value
    return value
def _chunks(
    values: Sequence[str],
    size: int,
) -> list[list[str]]:
    if size <= 0:
        raise ValueError(
            "chunk size must be greater than zero"
        )
    return [
        list(values[index:index + size])
        for index in range(
            0,
            len(values),
            size,
        )
    ]
