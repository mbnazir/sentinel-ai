from datetime import date
from unittest.mock import patch

import httpx
import pytest
import asyncio

from app.connectors.quartz import QuartzConnectorConfig, QuartzConnectorError, QuartzRestConnector
from app.domain.data_sources import ActivityDataSource


def make_connector(handler):
    connector = QuartzRestConnector(
        QuartzConnectorConfig(
            base_url="https://quartz.test",
            sessions_path="/login-sessions",
            activities_path="/activities",
        )
    )

    def mock_client():
        return httpx.AsyncClient(
            transport=httpx.MockTransport(handler),
            base_url="https://quartz.test",
        )

    return connector, mock_client


@pytest.mark.asyncio
async def test_quartz_connector_normalizes_session_and_activity_sources() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("login-sessions"):
            return httpx.Response(
                200,
                json={
                    "items": [
                        {
                            "id": 101,
                            "agent_id": 44,
                            "supervisor_id": 7,
                            "shift_date": "2026-08-26",
                            "start_date": "2026-08-26T08:00:00Z",
                            "end_date": "2026-08-26T16:00:00Z",
                            "ready_for_payroll": 1,
                            "payroll_adjusted": 0,
                            "multiple_logins": 2,
                        }
                    ]
                },
            )
        if request.url.path.endswith("activities"):
            return httpx.Response(
                200,
                json={
                    "items": [
                        {
                            "id": 501,
                            "login_session_id": 101,
                            "agent_id": 44,
                            "data_source_id": 3,
                            "activity_type_id": 9,
                            "source_id": 2,
                            "start_time": "2026-08-26T08:00:00Z",
                            "end_time": "2026-08-26T09:00:00Z",
                            "duration": 3600,
                            "inactivity_time": 0,
                        }
                    ]
                },
            )
        raise AssertionError(f"Unexpected request path: {request.url.path}")

    connector, mock_client = make_connector(handler)
    with patch.object(connector, "_client", side_effect=mock_client):
        sessions = [
            item
            async for item in connector.iter_sessions(
                shift_date_from=date(2026, 8, 26),
                shift_date_to=date(2026, 8, 26),
            )
        ]
        activities = [
            item async for item in connector.iter_activities(login_session_ids=["101"])
        ]

    assert len(sessions) == 1
    assert len(activities) == 1
    assert sessions[0].source_session_id == "101"
    assert sessions[0].ready_for_payroll is True
    assert sessions[0].multiple_logins == 2
    assert activities[0].data_source_id is ActivityDataSource.SUPERVISOR
    assert activities[0].duration_seconds == 3600


@pytest.mark.asyncio
async def test_quartz_connector_follows_cursor_pagination() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if request.url.params.get("cursor") == "next":
            return httpx.Response(200, json={"items": [], "next_cursor": None})
        return httpx.Response(
            200,
            json={
                "items": [
                    {
                        "id": 101,
                        "agent_id": 44,
                        "shift_date": "2026-08-26",
                        "start_date": "2026-08-26T08:00:00Z",
                    }
                ],
                "next_cursor": "next",
            },
        )

    connector, mock_client = make_connector(handler)
    with patch.object(connector, "_client", side_effect=mock_client):
        sessions = [
            item
            async for item in connector.iter_sessions(
                shift_date_from=date(2026, 8, 25),
                shift_date_to=date(2026, 8, 26),
            )
        ]

    assert len(sessions) == 1
    assert sessions[0].source_session_id == "101"
    assert calls == 2


@pytest.mark.asyncio
async def test_quartz_connector_rejects_unknown_data_source() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("activities")
        return httpx.Response(
            200,
            json={
                "items": [
                    {
                        "id": 501,
                        "login_session_id": 101,
                        "data_source_id": 99,
                        "activity_type_id": 1,
                        "start_time": "2026-08-26T08:00:00Z",
                        "end_time": None,
                        "duration": 60,
                    }
                ]
            },
        )

    connector, mock_client = make_connector(handler)
    with patch.object(connector, "_client", side_effect=mock_client):
        with pytest.raises(QuartzConnectorError, match="Unsupported Quartz data_source_id"):
            _ = [
                item async for item in connector.iter_activities(login_session_ids=["101"])
            ]


def test_session_normalization_accepts_optional_organizational_dimensions() -> None:
    connector = QuartzRestConnector(
        QuartzConnectorConfig(base_url="https://quartz.test")
    )
    session = connector._normalize_session(
        {
            "id": 99,
            "agent_id": 7,
            "supervisor_id": 8,
            "manager_id": 9,
            "site_id": "PK-LHE",
            "site_name": "Lahore",
            "team_id": "T-12",
            "shift_date": "2026-08-27",
            "start_date": "2026-08-27T08:00:00+00:00",
        }
    )
    assert session.manager_id == "9"
    assert session.site_id == "PK-LHE"
    assert session.site_name == "Lahore"
    assert session.team_id == "T-12"


@pytest.mark.asyncio
async def test_read_timeout_retries_then_succeeds(monkeypatch) -> None:
    calls = 0

    def handler(request):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise httpx.ReadTimeout("timeout", request=request)
        return httpx.Response(200, json={"items": []})

    connector, mock_client = make_connector(handler)
    connector.request_max_attempts = 2
    sleeps = []
    async def no_sleep(delay):
        sleeps.append(delay)
    monkeypatch.setattr(asyncio, "sleep", no_sleep)
    with patch.object(connector, "_client", side_effect=mock_client):
        page = await connector.fetch_sessions_page(
            shift_date_from=date(2026, 8, 26), shift_date_to=date(2026, 8, 26))
    assert page.items == []
    assert page.attempts == 2
    assert calls == 2
    assert len(sleeps) == 1


@pytest.mark.asyncio
async def test_retry_budget_exhaustion_is_bounded(monkeypatch) -> None:
    calls = 0
    def handler(request):
        nonlocal calls
        calls += 1
        raise httpx.ReadTimeout("timeout", request=request)
    connector, mock_client = make_connector(handler)
    connector.request_max_attempts = 2
    async def no_sleep(_):
        return None
    monkeypatch.setattr(asyncio, "sleep", no_sleep)
    with patch.object(connector, "_client", side_effect=mock_client):
        with pytest.raises(QuartzConnectorError) as error:
            await connector.fetch_sessions_page(shift_date_from=date(2026, 8, 26),
                                                shift_date_to=date(2026, 8, 26))
    assert calls == 2
    assert error.value.failure_category == "read_timeout"
    assert error.value.attempts == 2


@pytest.mark.asyncio
async def test_http_429_honors_retry_after(monkeypatch) -> None:
    calls = 0
    delays = []
    def handler(request):
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(429, headers={"Retry-After": "2"})
        return httpx.Response(200, json={"items": []})
    async def no_sleep(delay):
        delays.append(delay)
    monkeypatch.setattr(asyncio, "sleep", no_sleep)
    monkeypatch.setattr("app.connectors.quartz.rest.random.uniform", lambda a, b: 0)
    connector, mock_client = make_connector(handler)
    with patch.object(connector, "_client", side_effect=mock_client):
        page = await connector.fetch_sessions_page(shift_date_from=date(2026, 8, 26),
                                                   shift_date_to=date(2026, 8, 26))
    assert page.attempts == 2
    assert delays == [2.0]


@pytest.mark.asyncio
async def test_http_401_is_not_retried(monkeypatch) -> None:
    calls = 0
    def handler(request):
        nonlocal calls
        calls += 1
        return httpx.Response(401)
    async def no_sleep(_):
        return None
    monkeypatch.setattr(asyncio, "sleep", no_sleep)
    connector, mock_client = make_connector(handler)
    connector.request_max_attempts = 5
    with patch.object(connector, "_client", side_effect=mock_client):
        with pytest.raises(QuartzConnectorError) as error:
            await connector.fetch_sessions_page(shift_date_from=date(2026, 8, 26),
                                                shift_date_to=date(2026, 8, 26))
    assert calls == 1
    assert error.value.http_status == 401


@pytest.mark.asyncio
async def test_repeated_pagination_cursor_is_rejected() -> None:
    calls = 0
    def handler(request):
        nonlocal calls
        calls += 1
        return httpx.Response(200, json={"items": [], "next_cursor": "repeat"})
    connector, mock_client = make_connector(handler)
    with patch.object(connector, "_client", side_effect=mock_client):
        with pytest.raises(QuartzConnectorError, match="repeated pagination cursor"):
            _ = [item async for item in connector.iter_sessions(
                shift_date_from=date(2026, 8, 26), shift_date_to=date(2026, 8, 26))]
    assert calls == 2
