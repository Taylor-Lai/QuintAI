"""增加组织级共享模板数据结构。"""

import sqlalchemy as sa
from alembic import op

revision = "20260731_0008"
down_revision = "20260731_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "template_definitions",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("organization_id", sa.String(32), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("owner_id", sa.String(32), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("category", sa.String(80), nullable=False),
        sa.Column("scene", sa.String(120), nullable=False, server_default=""),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("output_format", sa.String(80), nullable=False, server_default="Excel / 在线表单"),
        sa.Column("tags", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("fields", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    for column in ("organization_id", "owner_id", "name", "category"):
        op.create_index(f"ix_template_definitions_{column}", "template_definitions", [column])


def downgrade() -> None:
    op.drop_table("template_definitions")
