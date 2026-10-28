from datetime import UTC, date, datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.weekly.activity_models import ComparisonStatus
from app.weekly.activity_repository import load_activity_comparison


@pytest.mark.asyncio
async def test_activity_lookup_binds_full_session_run_and_employee_key():
    run_id = uuid4()
    session = SimpleNamespace(source_system="quartz", source_session_id="s1", agent_id="e1",
                              shift_date=date(2026, 8, 25))
    stamp = datetime(2026, 8, 25, 10, tzinfo=UTC)
    activity_rows = [
        SimpleNamespace(source_activity_id="a", data_source_id=2, activity_type_id=1,
            start_at=stamp, end_at=stamp.replace(minute=5), duration_seconds=300,
            comment=None, source_created_at=None, source_updated_at=None, source_system="quartz",
            source_session_id="s1", ingestion_run_id=run_id),
        SimpleNamespace(source_activity_id="b", data_source_id=3, activity_type_id=1,
            start_at=stamp, end_at=stamp.replace(minute=5), duration_seconds=300,
            comment=None, source_created_at=None, source_updated_at=None, source_system="quartz",
            source_session_id="s1", ingestion_run_id=run_id),
    ]
    first_result = SimpleNamespace(scalar_one_or_none=lambda: session)
    second_result = SimpleNamespace(scalars=lambda: iter(activity_rows))
    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[first_result, second_result])

    result = await load_activity_comparison(db, ingestion_run_id=run_id, employee_id="e1",
        day=date(2026, 8, 26), source_session_id="s1")

    assert result.readiness.status == ComparisonStatus.READY
    assert result.net_covered_seconds == Decimal(0)
    statements = [call.args[0] for call in db.execute.await_args_list]
    compiled = [statement.compile().params for statement in statements]
    assert any(run_id in params.values() for params in compiled)
    assert any("e1" in params.values() for params in compiled)
    assert any("s1" in params.values() for params in compiled)


@pytest.mark.asyncio
async def test_activity_lookup_returns_none_when_session_is_not_owned_or_in_run():
    db = AsyncMock()
    db.execute = AsyncMock(return_value=SimpleNamespace(scalar_one_or_none=lambda: None))
    result = await load_activity_comparison(db, ingestion_run_id=uuid4(), employee_id="other",
        day=date(2026, 8, 26), source_session_id="s1")
    assert result is None
    assert db.execute.await_count == 1
