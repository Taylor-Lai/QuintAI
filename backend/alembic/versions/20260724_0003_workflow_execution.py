"""增加工作流执行记录与复核规则快照。"""

import sqlalchemy as sa
from alembic import op

revision = "20260724_0003"
down_revision = "20260724_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("review_records", sa.Column("validation_rules", sa.JSON(), nullable=False, server_default="[]"))
    op.create_table(
        "workflow_runs",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("user_id", sa.String(32), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workflow_id", sa.String(32), sa.ForeignKey("workflow_definitions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_id", sa.String(32), sa.ForeignKey("document_records.id", ondelete="CASCADE"), nullable=False),
        sa.Column("task_id", sa.String(32), sa.ForeignKey("task_records.id", ondelete="SET NULL")),
        sa.Column("status", sa.String(20), nullable=False, server_default="queued"),
        sa.Column("current_node", sa.String(80), nullable=False, server_default="文档接收"),
        sa.Column("progress", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text()),
        sa.Column("started_at", sa.DateTime()),
        sa.Column("completed_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    for column in ("user_id", "workflow_id", "document_id", "task_id", "status"):
        op.create_index(f"ix_workflow_runs_{column}", "workflow_runs", [column])


def downgrade() -> None:
    op.drop_table("workflow_runs")
    op.drop_column("review_records", "validation_rules")
