"""persisted anomaly findings

Revision ID: 0026_persisted_anomaly_findings
Revises: 0023_behavior_intelligence
Create Date: 2026-07-06
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0026_persisted_anomaly_findings"
down_revision: str | None = "0023_behavior_intelligence"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "anomaly_findings",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("organization_id", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.String(100), nullable=False),
        sa.Column("window_days", sa.Integer(), nullable=False),
        sa.Column("as_of_date", sa.Date(), nullable=False),
        sa.Column("anomaly_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("severity", sa.String(50), nullable=False, server_default="none"),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("anomaly_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("details", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "organization_id",
            "entity_type",
            "entity_id",
            "window_days",
            "as_of_date",
            name="uq_anomaly_finding_entity_window",
        ),
    )
    op.create_index("ix_anomaly_findings_org_entity", "anomaly_findings", ["organization_id", "entity_type", "entity_id"])
    op.create_index("ix_anomaly_findings_score", "anomaly_findings", ["organization_id", "anomaly_score"])
    op.create_index("ix_anomaly_findings_active", "anomaly_findings", ["organization_id", "is_active"])


def downgrade() -> None:
    op.drop_index("ix_anomaly_findings_active", table_name="anomaly_findings")
    op.drop_index("ix_anomaly_findings_score", table_name="anomaly_findings")
    op.drop_index("ix_anomaly_findings_org_entity", table_name="anomaly_findings")
    op.drop_table("anomaly_findings")
