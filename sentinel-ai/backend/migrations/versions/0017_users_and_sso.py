"""users and sso

Revision ID: 0017_users_and_sso
Revises: 0013_normalized_timeline_activities
Create Date: 2026-07-06
"""

from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa

revision: str = "0017_users_and_sso"
down_revision: str | None = "0013_normalized_timeline_activities"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "sentinel_users",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("user_id", sa.String(100), nullable=False, unique=True),
        sa.Column("organization_id", sa.String(100), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=True),
        sa.Column("roles", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("auth_provider", sa.String(50), nullable=False, server_default="local"),
        sa.Column("external_subject", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_sentinel_users_email", "sentinel_users", ["email"])
    op.create_index("ix_sentinel_users_org", "sentinel_users", ["organization_id"])


def downgrade() -> None:
    op.drop_index("ix_sentinel_users_org", table_name="sentinel_users")
    op.drop_index("ix_sentinel_users_email", table_name="sentinel_users")
    op.drop_table("sentinel_users")
