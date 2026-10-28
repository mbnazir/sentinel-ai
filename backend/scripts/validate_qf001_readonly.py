"""Temporary, read-only QF-001 validation against the two named Quartz runs.

Run inside the existing API container:
    docker compose exec -T api python scripts/validate_qf001_readonly.py

This runner sets the PostgreSQL transaction read-only before its first query. It
does not create scans, findings, audit events, or any other database rows.
"""

from __future__ import annotations

import asyncio
import json
import re
from datetime import date
from uuid import UUID

from sqlalchemy import and_, func, select, text
from sqlalchemy.orm import aliased
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import settings
from app.infrastructure.models import (
    IngestionProgressModel,
    IngestionRunModel,
    SessionSnapshotModel,
)
from app.rules.historical_comparison import evaluate_manager_decision_reversals_detailed
from app.workers.pipeline import observation_from_session_snapshot


EARLIER_RUN_ID = "a62525d0-3d22-4944-a4f3-5cc1540854f7"
LATER_RUN_ID = "026961c1-9442-4818-af5f-620c0be3d62f"
RUN_UUIDS = (UUID(EARLIER_RUN_ID), UUID(LATER_RUN_ID))
SHIFT_DATE = date(2026, 8, 26)
EXPECTED_SESSION_IDS = {
    "180660384",
    "180667650",
    "180689901",
    "180690354",
    "180691869",
}


async def main() -> int:
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    try:
        async with engine.connect() as connection:
            async with connection.begin():
                # Must be the first SQL command in this transaction.
                await connection.execute(text("SET TRANSACTION READ ONLY"))
                async with AsyncSession(
                    bind=connection,
                    expire_on_commit=False,
                    autoflush=False,
                ) as db:
                    return await validate(db)
    finally:
        await engine.dispose()


async def validate(db: AsyncSession) -> int:
    run_ids = (EARLIER_RUN_ID, LATER_RUN_ID)
    runs = {
        str(row.id): row
        for row in (await db.execute(
            select(IngestionRunModel).where(IngestionRunModel.id.in_(RUN_UUIDS))
        )).scalars().all()
    }
    missing_runs = sorted(set(run_ids) - set(runs))
    if missing_runs:
        raise RuntimeError(f"Selected ingestion runs not found: {missing_runs}")

    progress_rows = {
        str(row.ingestion_run_id): row
        for row in (await db.execute(
            select(IngestionProgressModel).where(
                IngestionProgressModel.ingestion_run_id.in_(RUN_UUIDS)
            )
        )).scalars().all()
    }
    sessions: dict[str, list[SessionSnapshotModel]] = {}
    stored_counts: dict[str, int] = {}
    for run_id in run_ids:
        count = await db.scalar(
            select(func.count()).select_from(SessionSnapshotModel).where(
                SessionSnapshotModel.ingestion_run_id == UUID(run_id)
            )
        )
        stored_counts[run_id] = int(count or 0)
        sessions[run_id] = list((await db.execute(
            select(SessionSnapshotModel).where(
                SessionSnapshotModel.ingestion_run_id == UUID(run_id),
            )
        )).scalars().all())

    earlier_all_observations = [
        observation_from_session_snapshot(row) for row in sessions[EARLIER_RUN_ID]
    ]
    later_all_observations = [
        observation_from_session_snapshot(row) for row in sessions[LATER_RUN_ID]
    ]
    all_dates_comparison = evaluate_manager_decision_reversals_detailed(
        earlier_all_observations,
        later_all_observations,
        earlier_run_id=EARLIER_RUN_ID,
        later_run_id=LATER_RUN_ID,
    )
    earlier_date_rows = [row for row in sessions[EARLIER_RUN_ID] if row.shift_date == SHIFT_DATE]
    later_date_rows = [row for row in sessions[LATER_RUN_ID] if row.shift_date == SHIFT_DATE]
    earlier_date_observations = [
        observation_from_session_snapshot(row) for row in earlier_date_rows
    ]
    later_date_observations = [
        observation_from_session_snapshot(row) for row in later_date_rows
    ]
    date_comparison = evaluate_manager_decision_reversals_detailed(
        earlier_date_observations,
        later_date_observations,
        earlier_run_id=EARLIER_RUN_ID,
        later_run_id=LATER_RUN_ID,
    )

    earlier_alias = aliased(SessionSnapshotModel)
    later_alias = aliased(SessionSnapshotModel)
    raw_shared_pairs_all_dates = int(await db.scalar(
        select(func.count()).select_from(earlier_alias).join(
            later_alias,
            and_(
                earlier_alias.source_system == later_alias.source_system,
                earlier_alias.source_session_id == later_alias.source_session_id,
            ),
        ).where(
            earlier_alias.ingestion_run_id == RUN_UUIDS[0],
            later_alias.ingestion_run_id == RUN_UUIDS[1],
        )
    ) or 0)

    hash_failures = []
    all_rows = sessions[EARLIER_RUN_ID] + sessions[LATER_RUN_ID]
    all_observations = earlier_all_observations + later_all_observations
    for row, observation in zip(all_rows, all_observations, strict=True):
        if re.fullmatch(r"[0-9a-fA-F]{64}", row.content_hash or "") is None:
            hash_failures.append({
                "ingestion_run_id": str(row.ingestion_run_id),
                "snapshot_id": str(row.id),
                "source_session_id": row.source_session_id,
                "reason": "stored hash is not a 64-character hexadecimal SHA-256 digest",
            })
        elif not observation.content_hash_verified:
            hash_failures.append({
                "ingestion_run_id": str(row.ingestion_run_id),
                "snapshot_id": str(row.id),
                "source_session_id": row.source_session_id,
                "reason": "stored hash differs from canonical_hash(NormalizedLoginSession.model_dump(mode='json'))",
            })

    expected_transitions = {
        "180660384": "4->5",
        "180667650": "5->4",
        "180689901": "4->5",
        "180690354": "4->5",
        "180691869": "4->5",
    }
    actual_transitions = {
        finding.source_session_id: str(finding.metadata["transition"])
        for finding in date_comparison.findings
    }
    expected_candidate_hash_failures = [
        failure for failure in hash_failures
        if failure["source_session_id"] in EXPECTED_SESSION_IDS
    ]

    result = {
        "validation": "QF-001 real-data read-only comparison",
        "transaction_read_only": True,
        "write_operations": 0,
        "shift_date": str(SHIFT_DATE),
        "runs": {
            run_id: {
                "status": runs[run_id].status,
                "stored_session_count": stored_counts[run_id],
                "date_session_count": len(
                    [row for row in sessions[run_id] if row.shift_date == SHIFT_DATE]
                ),
                "completion_status": progress_rows[run_id].completion_status
                if run_id in progress_rows else "CHECKPOINTS_UNAVAILABLE",
                "reconciliation_status": progress_rows[run_id].reconciliation_status
                if run_id in progress_rows else "CHECKPOINTS_UNAVAILABLE",
            }
            for run_id in run_ids
        },
        "raw_shared_session_pairs_all_dates": raw_shared_pairs_all_dates,
        "evaluator_matched_pairs_all_dates": all_dates_comparison.matched_pairs_count,
        "evaluator_valid_comparisons_all_dates": all_dates_comparison.valid_comparisons_count,
        "date_matched_pairs": date_comparison.matched_pairs_count,
        "date_valid_comparisons": date_comparison.valid_comparisons_count,
        "date_excluded_pairs_by_reason": date_comparison.excluded_pair_counts,
        "date_excluded_pair_session_ids": date_comparison.excluded_pair_session_ids,
        "date_excluded_records_by_reason": date_comparison.excluded_record_counts,
        "all_dates_hash_validation_failures": hash_failures,
        "date_hash_validation_failures": [
            failure for failure in hash_failures
            if failure["source_session_id"] in {
                row.source_session_id for row in earlier_date_rows + later_date_rows
            }
        ],
        "findings_count": len(date_comparison.findings),
        "finding_session_ids_and_transitions": actual_transitions,
        "expected_finding_session_ids": sorted(EXPECTED_SESSION_IDS),
        "matches_expected": actual_transitions == expected_transitions,
        "canonical_hash": "app.application.snapshot_hash.canonical_hash",
    }
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    return 0 if (
        actual_transitions == expected_transitions
        and not expected_candidate_hash_failures
    ) else 2


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
