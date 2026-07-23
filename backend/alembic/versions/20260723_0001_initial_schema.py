"""创建初始生产数据结构。"""

import sqlalchemy as sa
from alembic import op

revision = "20260723_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("username", sa.String(50), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("nickname", sa.String(80)),
        sa.Column("gender", sa.String(10)),
        sa.Column("phone", sa.String(20)),
        sa.Column("account_status", sa.String(20), nullable=False, server_default="正常"),
        sa.Column("role", sa.String(20), nullable=False, server_default="普通用户"),
        sa.Column("token_version", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_login_at", sa.DateTime()),
        sa.Column("last_login_ip", sa.String(64)),
        sa.Column("last_activity_at", sa.DateTime()),
        sa.Column("remark", sa.Text()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("username"),
        sa.UniqueConstraint("email"),
    )
    for column in ("username", "email", "account_status", "role"):
        op.create_index(f"ix_users_{column}", "users", [column])
    op.create_table(
        "task_records",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("celery_task_id", sa.String(36), nullable=False, unique=True),
        sa.Column("user_id", sa.String(32), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kind", sa.String(30), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("progress", sa.Integer(), nullable=False),
        sa.Column("stage", sa.String(100), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("result_data", sa.JSON()),
        sa.Column("output_path", sa.Text()),
        sa.Column("output_name", sa.String(255)),
        sa.Column("error_code", sa.String(50)),
        sa.Column("error_message", sa.Text()),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("max_attempts", sa.Integer(), nullable=False),
        sa.Column("cancel_requested", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("started_at", sa.DateTime()),
        sa.Column("completed_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    for column in ("celery_task_id", "user_id", "kind", "status"):
        op.create_index(f"ix_task_records_{column}", "task_records", [column])
    op.create_table(
        "extraction_records",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("user_id", sa.String(32), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("task_id", sa.String(32), sa.ForeignKey("task_records.id", ondelete="SET NULL")),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("file_type", sa.String(20), nullable=False),
        sa.Column("fields_requested", sa.JSON(), nullable=False),
        sa.Column("extracted_data", sa.JSON(), nullable=False),
        sa.Column("content_preview", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    for column in ("user_id", "task_id", "filename", "status"):
        op.create_index(f"ix_extraction_records_{column}", "extraction_records", [column])


def downgrade() -> None:
    op.drop_table("extraction_records")
    op.drop_table("task_records")
    op.drop_table("users")
