"""scan worker orchestration
Revision ID: 0005_scan_worker_orchestration
Revises: 0004_scan_investigation_platform
"""
from alembic import op
import sqlalchemy as sa
revision="0005_scan_worker_orchestration"
down_revision="0004_scan_investigation_platform"
branch_labels=None
depends_on=None
def upgrade():
    op.add_column("analysis_scans",sa.Column("total_chunks",sa.Integer(),nullable=False,server_default="0"))
    op.add_column("analysis_scans",sa.Column("completed_chunks",sa.Integer(),nullable=False,server_default="0"))
    op.add_column("analysis_scans",sa.Column("failed_chunks",sa.Integer(),nullable=False,server_default="0"))
    op.add_column("analysis_scans",sa.Column("cancel_requested",sa.Boolean(),nullable=False,server_default=sa.false()))
    op.add_column("analysis_scans",sa.Column("rule_version",sa.String(50)))
    op.add_column("analysis_scans",sa.Column("engine_version",sa.String(50)))
def downgrade():
    for c in ["engine_version","rule_version","cancel_requested","failed_chunks","completed_chunks","total_chunks"]:
        op.drop_column("analysis_scans",c)
