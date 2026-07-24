"""将 Webhook 签名密钥改为可用于签名的加密存储。"""

import sqlalchemy as sa
from alembic import op

revision = "20260724_0005"
down_revision = "20260724_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("webhook_endpoints", sa.Column("secret_ciphertext", sa.Text()))


def downgrade() -> None:
    op.drop_column("webhook_endpoints", "secret_ciphertext")
