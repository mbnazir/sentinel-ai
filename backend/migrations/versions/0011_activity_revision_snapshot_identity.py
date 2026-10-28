"""include Quartz source-stage identity in activity snapshot uniqueness

Revision ID: 0011_activity_revision_snapshot_identity
Revises: 0010_ingestion_recovery_audit
"""
from collections.abc import Sequence

from alembic import op

revision: str = "0011_activity_revision_snapshot_identity"
down_revision: str | None = "0010_ingestion_recovery_audit"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # The previous key treated Quartz's alternative data-source timelines as
    # one row identity. Preserve existing rows while allowing the same source
    # activity/session to have distinct source-stage (revision) rows.
    op.drop_constraint("uq_activity_snapshot_run_source", "activity_snapshots", type_="unique")
    op.create_unique_constraint(
        "uq_activity_snapshot_run_session_revision",
        "activity_snapshots",
        ["ingestion_run_id", "source_system", "source_session_id", "source_activity_id", "data_source_id"],
    )


def downgrade() -> None:
    # Downgrade is safe only if no duplicate source_activity_id rows were
    # ingested across session/stage identities after this revision.
    op.drop_constraint("uq_activity_snapshot_run_session_revision", "activity_snapshots", type_="unique")
    op.create_unique_constraint(
        "uq_activity_snapshot_run_source",
        "activity_snapshots",
        ["ingestion_run_id", "source_system", "source_activity_id"],
    )
