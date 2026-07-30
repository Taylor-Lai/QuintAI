"""增加持久化知识图谱的实体、关系与证据模型。"""

import sqlalchemy as sa
from alembic import op

revision = "20260731_0007"
down_revision = "20260725_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "knowledge_entities",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("collection_id", sa.String(32), sa.ForeignKey("knowledge_collections.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entity_type", sa.String(40), nullable=False),
        sa.Column("canonical_name", sa.String(255), nullable=False),
        sa.Column("normalized_name", sa.String(255), nullable=False),
        sa.Column("aliases", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("attributes", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.7"),
        sa.Column("review_status", sa.String(20), nullable=False, server_default="unreviewed"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("collection_id", "entity_type", "normalized_name", name="uq_knowledge_entity_identity"),
    )
    for column in ("collection_id", "entity_type", "canonical_name", "normalized_name", "review_status"):
        op.create_index(f"ix_knowledge_entities_{column}", "knowledge_entities", [column])

    op.create_table(
        "knowledge_relations",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("collection_id", sa.String(32), sa.ForeignKey("knowledge_collections.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_entity_id", sa.String(32), sa.ForeignKey("knowledge_entities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_entity_id", sa.String(32), sa.ForeignKey("knowledge_entities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("relation_type", sa.String(60), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.7"),
        sa.Column("attributes", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("collection_id", "source_entity_id", "target_entity_id", "relation_type", name="uq_knowledge_relation_identity"),
    )
    for column in ("collection_id", "source_entity_id", "target_entity_id", "relation_type"):
        op.create_index(f"ix_knowledge_relations_{column}", "knowledge_relations", [column])

    op.create_table(
        "knowledge_evidence",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("collection_id", sa.String(32), sa.ForeignKey("knowledge_collections.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entity_id", sa.String(32), sa.ForeignKey("knowledge_entities.id", ondelete="CASCADE")),
        sa.Column("relation_id", sa.String(32), sa.ForeignKey("knowledge_relations.id", ondelete="CASCADE")),
        sa.Column("document_id", sa.String(32), sa.ForeignKey("document_records.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chunk_id", sa.String(32), sa.ForeignKey("knowledge_chunks.id", ondelete="SET NULL")),
        sa.Column("extraction_id", sa.String(32), sa.ForeignKey("extraction_records.id", ondelete="SET NULL")),
        sa.Column("field_name", sa.String(160)),
        sa.Column("snippet", sa.Text(), nullable=False, server_default=""),
        sa.Column("location", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.7"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("entity_id IS NOT NULL OR relation_id IS NOT NULL", name="ck_knowledge_evidence_target"),
    )
    for column in ("collection_id", "entity_id", "relation_id", "document_id", "chunk_id", "extraction_id"):
        op.create_index(f"ix_knowledge_evidence_{column}", "knowledge_evidence", [column])


def downgrade() -> None:
    op.drop_table("knowledge_evidence")
    op.drop_table("knowledge_relations")
    op.drop_table("knowledge_entities")
