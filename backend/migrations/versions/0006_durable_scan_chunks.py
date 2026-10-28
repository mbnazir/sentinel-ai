"""durable scan chunks
Revision ID: 0006_durable_scan_chunks
Revises: 0005_scan_worker_orchestration
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision="0006_durable_scan_chunks"; down_revision="0005_scan_worker_orchestration"; branch_labels=None; depends_on=None
def upgrade():
    op.create_table("scan_chunks",
      sa.Column("id",postgresql.UUID(as_uuid=True),primary_key=True),
      sa.Column("scan_id",postgresql.UUID(as_uuid=True),sa.ForeignKey("analysis_scans.id",ondelete="RESTRICT"),nullable=False),
      sa.Column("chunk_index",sa.Integer(),nullable=False),
      sa.Column("date_from",sa.Date(),nullable=False),sa.Column("date_to",sa.Date(),nullable=False),
      sa.Column("status",sa.String(30),nullable=False),sa.Column("attempt",sa.Integer(),nullable=False,server_default="0"),
      sa.Column("worker_id",sa.String(128)),sa.Column("started_at",sa.DateTime(timezone=True)),sa.Column("completed_at",sa.DateTime(timezone=True)),
      sa.Column("employee_days_processed",sa.Integer(),nullable=False,server_default="0"),
      sa.Column("findings_persisted",sa.Integer(),nullable=False,server_default="0"),
      sa.Column("checkpoint_json",postgresql.JSONB(),nullable=False,server_default=sa.text("'{}'::jsonb")),
      sa.Column("error_message",sa.Text()),sa.UniqueConstraint("scan_id","chunk_index",name="uq_scan_chunk_index"))
    op.create_index("ix_scan_chunks_scan_status","scan_chunks",["scan_id","status"])
def downgrade(): op.drop_table("scan_chunks")
