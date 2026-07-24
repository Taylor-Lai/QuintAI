"""增加文档工作台、复核与工作流数据结构。"""

import sqlalchemy as sa
from alembic import op

revision = "20260724_0002"
down_revision = "20260723_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "document_records",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("user_id", sa.String(32), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("file_type", sa.String(30), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("storage_path", sa.Text(), nullable=False),
        sa.Column("source", sa.String(30), nullable=False, server_default="upload"),
        sa.Column("category", sa.String(80), nullable=False, server_default="未分类"),
        sa.Column("status", sa.String(30), nullable=False, server_default="ready"),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("content_preview", sa.Text(), nullable=False, server_default=""),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    for column in ("user_id", "filename", "file_type", "source", "category", "status"):
        op.create_index(f"ix_document_records_{column}", "document_records", [column])

    op.add_column("extraction_records", sa.Column("document_id", sa.String(32)))
    op.create_foreign_key(
        "fk_extraction_records_document_id", "extraction_records", "document_records", ["document_id"], ["id"], ondelete="SET NULL"
    )
    op.create_index("ix_extraction_records_document_id", "extraction_records", ["document_id"])

    op.create_table(
        "review_records",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("user_id", sa.String(32), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_id", sa.String(32), sa.ForeignKey("document_records.id", ondelete="CASCADE")),
        sa.Column("extraction_id", sa.String(32), sa.ForeignKey("extraction_records.id", ondelete="SET NULL"), unique=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("priority", sa.String(20), nullable=False, server_default="normal"),
        sa.Column("fields", sa.JSON(), nullable=False),
        sa.Column("validation_results", sa.JSON(), nullable=False),
        sa.Column("note", sa.Text()),
        sa.Column("reviewed_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    for column in ("user_id", "document_id", "extraction_id", "status", "priority"):
        op.create_index(f"ix_review_records_{column}", "review_records", [column])

    op.create_table(
        "workflow_definitions",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("user_id", sa.String(32), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("nodes", sa.JSON(), nullable=False),
        sa.Column("rules", sa.JSON(), nullable=False),
        sa.Column("runs_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    for column in ("user_id", "name", "status"):
        op.create_index(f"ix_workflow_definitions_{column}", "workflow_definitions", [column])


def downgrade() -> None:
    op.drop_table("workflow_definitions")
    op.drop_table("review_records")
    op.drop_index("ix_extraction_records_document_id", table_name="extraction_records")
    op.drop_constraint("fk_extraction_records_document_id", "extraction_records", type_="foreignkey")
    op.drop_column("extraction_records", "document_id")
    op.drop_table("document_records")
