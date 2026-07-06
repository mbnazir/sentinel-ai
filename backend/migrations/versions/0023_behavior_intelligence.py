"""behavior intelligence

Revision ID: 0023_behavior_intelligence
Revises: 0020_normalized_quartz_ingestion
Create Date: 2026-07-06
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0023_behavior_intelligence"
down_revision: str | None = "0020_normalized_quartz_ingestion"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "behavior_feature_snapshots",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("organization_id", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.String(100), nullable=False),
        sa.Column("window_days", sa.Integer(), nullable=False),
        sa.Column("as_of_date", sa.Date(), nullable=False),
        sa.Column("session_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("average_risk_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("max_risk_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("high_risk_session_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("inserted_activity_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("deleted_activity_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("extended_activity_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("payroll_adjustment_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("manual_added_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rule_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("behavior_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("behavior_level", sa.String(50), nullable=False, server_default="normal"),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "organization_id",
            "entity_type",
            "entity_id",
            "window_days",
            "as_of_date",
            name="uq_behavior_feature_snapshot",
        ),
    )
    op.create_index("ix_behavior_snapshot_org_entity", "behavior_feature_snapshots", ["organization_id", "entity_type", "entity_id"])
    op.create_index("ix_behavior_snapshot_score", "behavior_feature_snapshots", ["behavior_score"])

    op.create_table(
        "behavior_peer_deviations",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("organization_id", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.String(100), nullable=False),
        sa.Column("metric_name", sa.String(100), nullable=False),
        sa.Column("window_days", sa.Integer(), nullable=False),
        sa.Column("as_of_date", sa.Date(), nullable=False),
        sa.Column("entity_value", sa.Float(), nullable=False),
        sa.Column("peer_average", sa.Float(), nullable=False),
        sa.Column("peer_stddev", sa.Float(), nullable=False),
        sa.Column("z_score", sa.Float(), nullable=False),
        sa.Column("is_outlier", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint(
            "organization_id",
            "entity_type",
            "entity_id",
            "metric_name",
            "window_days",
            "as_of_date",
            name="uq_behavior_peer_deviation",
        ),
    )
    op.create_index("ix_behavior_deviation_outlier", "behavior_peer_deviations", ["organization_id", "is_outlier"])


def downgrade() -> None:
    op.drop_index("ix_behavior_deviation_outlier", table_name="behavior_peer_deviations")
    op.drop_table("behavior_peer_deviations")
    op.drop_index("ix_behavior_snapshot_score", table_name="behavior_feature_snapshots")
    op.drop_index("ix_behavior_snapshot_org_entity", table_name="behavior_feature_snapshots")
    op.drop_table("behavior_feature_snapshots")
