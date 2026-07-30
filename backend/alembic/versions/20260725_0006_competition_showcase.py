"""增加比赛展示所需的任务事件、证据检索、调度和 Webhook 投递记录。"""

import sqlalchemy as sa
from alembic import op

revision = "20260725_0006"
down_revision = "20260724_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("task_records", sa.Column("completed_steps", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("task_records", sa.Column("total_steps", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("task_records", sa.Column("quality_report", sa.JSON(), nullable=False, server_default="{}"))
    op.add_column("task_records", sa.Column("evidence_summary", sa.JSON(), nullable=False, server_default="{}"))
    op.create_table(
        "task_events",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("task_id", sa.String(32), sa.ForeignKey("task_records.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("node_code", sa.String(80), nullable=False),
        sa.Column("label", sa.String(160), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("progress", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("detail", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("started_at", sa.DateTime()),
        sa.Column("completed_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    for column in ("task_id", "sequence", "node_code", "status"):
        op.create_index(f"ix_task_events_{column}", "task_events", [column])

    op.create_table(
        "knowledge_chunks",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("collection_id", sa.String(32), sa.ForeignKey("knowledge_collections.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_id", sa.String(32), sa.ForeignKey("document_records.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("location", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("embedding", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("collection_id", "document_id", "chunk_index", name="uq_knowledge_chunk"),
    )
    op.create_index("ix_knowledge_chunks_collection_id", "knowledge_chunks", ["collection_id"])
    op.create_index("ix_knowledge_chunks_document_id", "knowledge_chunks", ["document_id"])

    op.create_table(
        "webhook_deliveries",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("organization_id", sa.String(32), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("endpoint_id", sa.String(32), sa.ForeignKey("webhook_endpoints.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event", sa.String(80), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="queued"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("payload", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("response_status", sa.Integer()),
        sa.Column("error_message", sa.Text()),
        sa.Column("delivered_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    for column in ("organization_id", "endpoint_id", "event", "status", "created_at"):
        op.create_index(f"ix_webhook_deliveries_{column}", "webhook_deliveries", [column])

    with op.batch_alter_table("automation_schedules") as batch_op:
        batch_op.add_column(sa.Column("document_id", sa.String(32)))
        batch_op.create_foreign_key(
            "fk_automation_schedules_document_id",
            "document_records",
            ["document_id"],
            ["id"],
            ondelete="CASCADE",
        )
    op.add_column("automation_schedules", sa.Column("last_status", sa.String(20)))
    op.create_index("ix_automation_schedules_document_id", "automation_schedules", ["document_id"])


def downgrade() -> None:
    op.drop_index("ix_automation_schedules_document_id", table_name="automation_schedules")
    with op.batch_alter_table("automation_schedules") as batch_op:
        batch_op.drop_column("last_status")
        batch_op.drop_constraint("fk_automation_schedules_document_id", type_="foreignkey")
        batch_op.drop_column("document_id")
    op.drop_table("webhook_deliveries")
    op.drop_table("knowledge_chunks")
    op.drop_table("task_events")
    with op.batch_alter_table("task_records") as batch_op:
        batch_op.drop_column("evidence_summary")
        batch_op.drop_column("quality_report")
        batch_op.drop_column("total_steps")
        batch_op.drop_column("completed_steps")
