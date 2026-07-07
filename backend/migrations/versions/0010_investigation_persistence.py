"""investigation persistence

Revision ID: 0010_investigation_persistence
Revises: 0001_initial
Create Date: 2026-07-06
"""
from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa

revision: str = "0010_investigation_persistence"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

def upgrade() -> None:
    op.create_table("investigation_cases",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("case_id", sa.String(64), nullable=False, unique=True),
        sa.Column("organization_id", sa.String(100), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_id", sa.String(100), nullable=False),
        sa.Column("risk_score", sa.Integer(), nullable=False),
        sa.Column("priority", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("assigned_to", sa.String(100), nullable=True),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_table("investigation_evidence_links",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("case_id", sa.String(64), sa.ForeignKey("investigation_cases.case_id"), nullable=False),
        sa.Column("evidence_id", sa.String(255), nullable=False),
        sa.Column("evidence_type", sa.String(100), nullable=False),
        sa.Column("source", sa.String(255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False))
    op.create_table("investigation_comments",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("case_id", sa.String(64), sa.ForeignKey("investigation_cases.case_id"), nullable=False),
        sa.Column("author_id", sa.String(100), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_table("investigation_narratives",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("case_id", sa.String(64), sa.ForeignKey("investigation_cases.case_id"), nullable=False),
        sa.Column("executive_summary", sa.Text(), nullable=False),
        sa.Column("key_findings", sa.JSON(), nullable=False),
        sa.Column("evidence_summary", sa.JSON(), nullable=False),
        sa.Column("recommended_next_steps", sa.JSON(), nullable=False),
        sa.Column("limitations", sa.JSON(), nullable=False),
        sa.Column("raw_model_output", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))

def downgrade() -> None:
    op.drop_table("investigation_narratives")
    op.drop_table("investigation_comments")
    op.drop_table("investigation_evidence_links")
    op.drop_table("investigation_cases")
