from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1 import routes_investigations as routes
from app.core.auth import Principal, Role
from app.investigations.models import CaseCreate, CaseStatus, CaseUpdate
from app.investigations.service import update_case


def case():
    return SimpleNamespace(
        id=uuid4(), case_number="SNT-TEST", title="Synthetic review",
        status="open", disposition="undetermined", assigned_to="reviewer",
        created_by="reviewer", created_at=datetime.now(UTC), updated_at=datetime.now(UTC),
    )


@pytest.mark.asyncio
async def test_case_update_uses_authenticated_actor(monkeypatch):
    row = case()
    update = AsyncMock(return_value=row)
    monkeypatch.setattr(routes, "update_case", update)
    principal = Principal(subject="signed-in-reviewer", role=Role.INVESTIGATOR)
    await routes.patch_case(
        row.id, CaseUpdate(status=CaseStatus.IN_REVIEW, actor="forged-actor"),
        db=object(), principal=principal,
    )
    assert update.await_args.args[2].actor == "signed-in-reviewer"


@pytest.mark.asyncio
async def test_case_creation_uses_authenticated_actor(monkeypatch):
    create = AsyncMock(return_value=case())
    monkeypatch.setattr(routes, "create_case", create)
    await routes.post_case(
        CaseCreate(title="Synthetic review", created_by="forged-actor"), db=object(),
        principal=Principal(subject="signed-in-reviewer", role=Role.INVESTIGATOR),
    )
    assert create.await_args.args[1].created_by == "signed-in-reviewer"


@pytest.mark.asyncio
async def test_repeated_transition_without_note_does_not_duplicate_audit():
    row = case()
    db = AsyncMock(spec=AsyncSession)
    db.get.return_value = row
    payload = CaseUpdate(status=CaseStatus.IN_REVIEW, actor="reviewer")
    await update_case(db, row.id, payload)
    updated_at = row.updated_at
    await update_case(db, row.id, payload)
    assert row.status == "in_review"
    assert row.updated_at == updated_at
    assert db.add.call_count == 1
    assert db.commit.await_count == 1
    assert db.get.await_args.kwargs == {"with_for_update": True, "populate_existing": True}


@pytest.mark.asyncio
async def test_note_without_status_change_is_retained():
    row = case()
    db = AsyncMock(spec=AsyncSession)
    db.get.return_value = row
    await update_case(db, row.id, CaseUpdate(actor="reviewer", note="Requested source audit"))
    event = db.add.call_args.args[0]
    assert event.actor == "reviewer"
    assert event.event_json["note"] == "Requested source audit"
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_linked_findings_query_is_scoped_to_case():
    row = case()
    db = AsyncMock(spec=AsyncSession)
    db.get.return_value = row
    db.execute.return_value = SimpleNamespace(
        scalars=lambda: SimpleNamespace(all=lambda: []),
    )
    assert await routes.get_case_findings(row.id, db=db) == []
    query = db.execute.await_args.args[0].compile(dialect=postgresql.dialect())
    assert row.id in query.params.values()
    assert "case_findings.case_id =" in str(query)
    assert "case_findings.finding_id = durable_findings.id" in str(query)


@pytest.mark.asyncio
async def test_missing_case_returns_404_for_linked_findings():
    db = AsyncMock(spec=AsyncSession)
    db.get.return_value = None
    with pytest.raises(HTTPException) as exc:
        await routes.get_case_findings(uuid4(), db=db)
    assert exc.value.status_code == 404
    db.execute.assert_not_awaited()
