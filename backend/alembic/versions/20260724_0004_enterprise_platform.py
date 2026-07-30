"""增加企业组织、协作、集成、知识库、配额与运维数据结构。"""

import sqlalchemy as sa
from alembic import op

revision = "20260724_0004"
down_revision = "20260724_0003"
branch_labels = None
depends_on = None


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("owner_id", sa.String(32), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("slug", sa.String(80), nullable=False, unique=True),
        sa.Column("plan", sa.String(30), nullable=False, server_default="starter"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("settings", sa.JSON(), nullable=False, server_default="{}"),
        *_timestamps(),
    )
    op.create_index("ix_organizations_owner_id", "organizations", ["owner_id"])
    op.create_index("ix_organizations_slug", "organizations", ["slug"], unique=True)
    op.create_index("ix_organizations_plan", "organizations", ["plan"])
    op.create_index("ix_organizations_status", "organizations", ["status"])
    op.add_column("users", sa.Column("active_organization_id", sa.String(32)))
    op.create_index("ix_users_active_organization_id", "users", ["active_organization_id"])
    for table in (
        "extraction_records",
        "task_records",
        "document_records",
        "review_records",
        "workflow_definitions",
        "workflow_runs",
    ):
        with op.batch_alter_table(table) as batch_op:
            batch_op.add_column(sa.Column("organization_id", sa.String(32)))
            batch_op.create_foreign_key(
                f"fk_{table}_organization_id",
                "organizations",
                ["organization_id"],
                ["id"],
                ondelete="CASCADE",
            )
        op.create_index(f"ix_{table}_organization_id", table, ["organization_id"])

    op.create_table(
        "organization_members",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column(
            "organization_id", sa.String(32), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("user_id", sa.String(32), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="member"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("joined_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("organization_id", "user_id", name="uq_organization_member"),
    )
    for col in ("organization_id", "user_id", "role", "status"):
        op.create_index(f"ix_organization_members_{col}", "organization_members", [col])
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column(
            "organization_id", sa.String(32), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("user_id", sa.String(32), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("action", sa.String(80), nullable=False),
        sa.Column("resource_type", sa.String(40), nullable=False),
        sa.Column("resource_id", sa.String(64)),
        sa.Column("detail", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("ip_address", sa.String(64)),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    for col in ("organization_id", "user_id", "action", "resource_type", "resource_id", "created_at"):
        op.create_index(f"ix_audit_logs_{col}", "audit_logs", [col])
    op.create_table(
        "document_versions",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column(
            "document_id", sa.String(32), sa.ForeignKey("document_records.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("user_id", sa.String(32), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("storage_path", sa.Text(), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("checksum", sa.String(64), nullable=False),
        sa.Column("note", sa.String(500), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("document_id", "version", name="uq_document_version"),
    )
    op.create_index("ix_document_versions_document_id", "document_versions", ["document_id"])
    op.create_index("ix_document_versions_user_id", "document_versions", ["user_id"])
    op.create_table(
        "workflow_versions",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column(
            "workflow_id", sa.String(32), sa.ForeignKey("workflow_definitions.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("user_id", sa.String(32), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("snapshot", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("note", sa.String(500), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("workflow_id", "version", name="uq_workflow_version"),
    )
    op.create_index("ix_workflow_versions_workflow_id", "workflow_versions", ["workflow_id"])
    op.create_index("ix_workflow_versions_user_id", "workflow_versions", ["user_id"])
    op.create_table(
        "collaboration_comments",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column(
            "organization_id", sa.String(32), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("user_id", sa.String(32), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("resource_type", sa.String(40), nullable=False),
        sa.Column("resource_id", sa.String(64), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("mentions", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("resolved", sa.Boolean(), nullable=False, server_default=sa.false()),
        *_timestamps(),
    )
    for col in ("organization_id", "user_id", "resource_type", "resource_id", "resolved"):
        op.create_index(f"ix_collaboration_comments_{col}", "collaboration_comments", [col])
    op.create_table(
        "notifications",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("user_id", sa.String(32), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kind", sa.String(40), nullable=False),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
        sa.Column("link", sa.String(500)),
        sa.Column("read_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    for col in ("user_id", "kind", "created_at"):
        op.create_index(f"ix_notifications_{col}", "notifications", [col])
    op.create_table(
        "api_credentials",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column(
            "organization_id", sa.String(32), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("user_id", sa.String(32), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("prefix", sa.String(16), nullable=False),
        sa.Column("key_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("scopes", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("expires_at", sa.DateTime()),
        sa.Column("last_used_at", sa.DateTime()),
        sa.Column("revoked_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    for col in ("organization_id", "user_id", "prefix"):
        op.create_index(f"ix_api_credentials_{col}", "api_credentials", [col])
    op.create_table(
        "webhook_endpoints",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column(
            "organization_id", sa.String(32), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("url", sa.String(1000), nullable=False),
        sa.Column("secret_hash", sa.String(64), nullable=False),
        sa.Column("events", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        *_timestamps(),
    )
    op.create_index("ix_webhook_endpoints_organization_id", "webhook_endpoints", ["organization_id"])
    op.create_index("ix_webhook_endpoints_active", "webhook_endpoints", ["active"])
    op.create_table(
        "knowledge_collections",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column(
            "organization_id", sa.String(32), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("owner_id", sa.String(32), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("retrieval_mode", sa.String(30), nullable=False, server_default="hybrid"),
        *_timestamps(),
    )
    op.create_index("ix_knowledge_collections_organization_id", "knowledge_collections", ["organization_id"])
    op.create_index("ix_knowledge_collections_owner_id", "knowledge_collections", ["owner_id"])
    op.create_table(
        "knowledge_items",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column(
            "collection_id",
            sa.String(32),
            sa.ForeignKey("knowledge_collections.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "document_id", sa.String(32), sa.ForeignKey("document_records.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("status", sa.String(20), nullable=False, server_default="indexed"),
        sa.Column("chunk_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("collection_id", "document_id", name="uq_knowledge_item"),
    )
    for col in ("collection_id", "document_id", "status"):
        op.create_index(f"ix_knowledge_items_{col}", "knowledge_items", [col])
    op.create_table(
        "automation_schedules",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column(
            "organization_id", sa.String(32), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "workflow_id", sa.String(32), sa.ForeignKey("workflow_definitions.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("user_id", sa.String(32), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("cron_expression", sa.String(80), nullable=False),
        sa.Column("timezone", sa.String(50), nullable=False, server_default="Asia/Shanghai"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("retry_limit", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("last_run_at", sa.DateTime()),
        sa.Column("next_run_at", sa.DateTime()),
        *_timestamps(),
    )
    for col in ("organization_id", "workflow_id", "user_id", "status"):
        op.create_index(f"ix_automation_schedules_{col}", "automation_schedules", [col])
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column(
            "organization_id",
            sa.String(32),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("plan", sa.String(30), nullable=False, server_default="starter"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("limits", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("usage", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("period_start", sa.DateTime(), nullable=False),
        sa.Column("period_end", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_subscriptions_organization_id", "subscriptions", ["organization_id"], unique=True)
    op.create_table(
        "backup_records",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column(
            "organization_id", sa.String(32), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("user_id", sa.String(32), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="completed"),
        sa.Column("storage_path", sa.Text(), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("checksum", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    for col in ("organization_id", "user_id", "status"):
        op.create_index(f"ix_backup_records_{col}", "backup_records", [col])


def downgrade() -> None:
    for table in (
        "backup_records",
        "subscriptions",
        "automation_schedules",
        "knowledge_items",
        "knowledge_collections",
        "webhook_endpoints",
        "api_credentials",
        "notifications",
        "collaboration_comments",
        "workflow_versions",
        "document_versions",
        "audit_logs",
        "organization_members",
    ):
        op.drop_table(table)
    for table in (
        "extraction_records",
        "task_records",
        "document_records",
        "review_records",
        "workflow_definitions",
        "workflow_runs",
    ):
        op.drop_index(f"ix_{table}_organization_id", table_name=table)
        with op.batch_alter_table(table) as batch_op:
            batch_op.drop_constraint(f"fk_{table}_organization_id", type_="foreignkey")
            batch_op.drop_column("organization_id")
    op.drop_index("ix_users_active_organization_id", table_name="users")
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("active_organization_id")
    op.drop_table("organizations")
