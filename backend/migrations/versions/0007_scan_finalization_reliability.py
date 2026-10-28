"""scan finalization reliability
Revision ID: 0007_scan_finalization_reliability
Revises: 0006_durable_scan_chunks
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision="0007_finalization"; down_revision="0006_durable_scan_chunks"; branch_labels=None; depends_on=None
def upgrade():
    op.add_column("analysis_scans",sa.Column("finalization_status",sa.String(30),nullable=False,server_default="pending"))
    op.add_column("analysis_scans",sa.Column("summary_json",postgresql.JSONB(),nullable=False,server_default=sa.text("'{}'::jsonb")))
    op.add_column("analysis_scans",sa.Column("dead_letter_count",sa.Integer(),nullable=False,server_default="0"))
def downgrade():
    op.drop_column("analysis_scans","dead_letter_count"); op.drop_column("analysis_scans","summary_json"); op.drop_column("analysis_scans","finalization_status")
