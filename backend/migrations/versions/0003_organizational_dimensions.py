"""organizational dimensions

Revision ID: 0003_organizational_dimensions
Revises: 0002_operational_snapshot_ledger
"""
from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa

revision: str = "0003_organizational_dimensions"
down_revision: str | None = "0002_operational_snapshot_ledger"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

def upgrade() -> None:
    op.add_column("session_snapshots", sa.Column("manager_id", sa.String(length=64), nullable=True))
    op.add_column("session_snapshots", sa.Column("site_id", sa.String(length=64), nullable=True))
    op.add_column("session_snapshots", sa.Column("site_name", sa.String(length=255), nullable=True))
    op.add_column("session_snapshots", sa.Column("team_id", sa.String(length=64), nullable=True))
    op.create_index("ix_session_snapshots_supervisor", "session_snapshots", ["supervisor_id", "shift_date"] )
    op.create_index("ix_session_snapshots_manager", "session_snapshots", ["manager_id", "shift_date"] )
    op.create_index("ix_session_snapshots_campaign", "session_snapshots", ["primary_campaign_id", "shift_date"] )
    op.create_index("ix_session_snapshots_site", "session_snapshots", ["site_id", "shift_date"] )

def downgrade() -> None:
    op.drop_index("ix_session_snapshots_site", table_name="session_snapshots")
    op.drop_index("ix_session_snapshots_campaign", table_name="session_snapshots")
    op.drop_index("ix_session_snapshots_manager", table_name="session_snapshots")
    op.drop_index("ix_session_snapshots_supervisor", table_name="session_snapshots")
    op.drop_column("session_snapshots", "team_id")
    op.drop_column("session_snapshots", "site_name")
    op.drop_column("session_snapshots", "site_id")
    op.drop_column("session_snapshots", "manager_id")
