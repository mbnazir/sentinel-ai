
import asyncio
from datetime import date
from uuid import UUID

from sqlalchemy import select

from app.core.database import get_session_factory
from app.application.connector_factory import build_connector
from app.application.normalized import NormalizedLoginSession
from app.application.snapshot_hash import canonical_hash
from app.infrastructure.models import (
    ConnectorModel,
    SessionSnapshotModel,
)

RUN_ID = UUID("a62525d0-3d22-4944-a4f3-5cc1540854f7")
CONNECTOR_ID = UUID("f23d324a-2530-47d1-bff0-d1cf8615d5d2")
SESSION_ID = "180583479"
SHIFT_DATE = date(2026, 8, 26)


async def main():
    async with get_session_factory()() as db:
        snapshot = (
            await db.execute(
                select(SessionSnapshotModel).where(
                    SessionSnapshotModel.ingestion_run_id == RUN_ID,
                    SessionSnapshotModel.source_system == "quartz",
                    SessionSnapshotModel.source_session_id == SESSION_ID,
                )
            )
        ).scalar_one()

        connector_row = (
            await db.execute(
                select(ConnectorModel).where(
                    ConnectorModel.id == CONNECTOR_ID
                )
            )
        ).scalar_one()

        historical_data = {
            field: (
                snapshot.metadata_json
                if field == "metadata"
                else getattr(snapshot, field)
            )
            for field in NormalizedLoginSession.model_fields
        }

        historical = NormalizedLoginSession.model_validate(
            historical_data
        )

        connector = build_connector(connector_row)

        try:
            page = await connector.fetch_sessions_page(
                shift_date_from=SHIFT_DATE,
                shift_date_to=SHIFT_DATE,
            )
        finally:
            await connector.close()

        current = next(
            (
                item
                for item in page.items
                if item.source_session_id == SESSION_ID
            ),
            None,
        )

        if current is None:
            print("Session not found in first Quartz page.")
            print("Further pagination would be required.")
            return

        historical_values = historical.model_dump(
            mode="json",
            exclude_none=False,
        )
        current_values = current.model_dump(
            mode="json",
            exclude_none=False,
        )

        print("Session:", SESSION_ID)
        print("Historical hash:", snapshot.content_hash)
        print("Current hash:", canonical_hash(current))
        print()

        sensitive_fields = {
            "agent_id",
            "supervisor_id",
            "manager_id",
            "agent_ip",
            "machine_hostname",
        }

        changed = []

        for field in historical_values:
            old = historical_values[field]
            new = current_values[field]

            if old == new:
                continue

            changed.append(field)

            if field in sensitive_fields:
                print(field, ": CHANGED (values masked)")
            elif field == "metadata":
                for key in sorted(set(old) | set(new)):
                    if old.get(key) != new.get(key):
                        print(
                            "metadata." + key,
                            ":",
                            old.get(key),
                            "->",
                            new.get(key),
                        )
            else:
                print(field, ":", old, "->", new)

        print()
        print("Changed field count:", len(changed))


asyncio.run(main())

