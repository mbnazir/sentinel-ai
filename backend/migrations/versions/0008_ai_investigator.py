"""ai investigator summaries
Revision ID: 0008_ai_investigator
Revises: 0007_scan_finalization_reliability
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision="0008_ai_investigator"; down_revision="0007_finalization"; branch_labels=None; depends_on=None
def upgrade():
    op.create_table("ai_investigator_summaries",
      sa.Column("id",postgresql.UUID(as_uuid=True),primary_key=True),
      sa.Column("case_id",postgresql.UUID(as_uuid=True),sa.ForeignKey("investigation_cases.id",ondelete="RESTRICT"),nullable=False),
      sa.Column("provider",sa.String(40),nullable=False),
      sa.Column("model",sa.String(120),nullable=False),
      sa.Column("prompt_version",sa.String(80),nullable=False),
      sa.Column("input_hash",sa.String(64),nullable=False),
      sa.Column("narrative",sa.Text(),nullable=False),
      sa.Column("requested_by",sa.String(128),nullable=False),
      sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now()))
    op.create_index("ix_ai_summary_case_created","ai_investigator_summaries",["case_id","created_at"])
def downgrade(): op.drop_table("ai_investigator_summaries")
