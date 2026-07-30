import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from docnexus.ai.knowledge_graph import KnowledgeGraphBuilder, export_graph_json
from docnexus.db import (
    Base,
    DocumentRecord,
    ExtractionRecord,
    KnowledgeCollection,
    KnowledgeEntity,
    KnowledgeItem,
    Organization,
    User,
)
from docnexus.services.knowledge_graph import (
    graph_context_for_query,
    rebuild_knowledge_graph,
    serialize_knowledge_graph,
)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class KnowledgeGraphSidecarTests(unittest.TestCase):
    def test_builds_graph_from_extraction_result_without_main_pipeline_flag(self) -> None:
        result = {
            "项目名称": "慧文融通",
            "负责人": "张三",
            "_meta": {
                "evidence": {
                    "负责人": {"chunk_id": 0, "snippet": "项目负责人为张三"}
                }
            },
        }

        graph = KnowledgeGraphBuilder().from_extraction_result(result)

        self.assertFalse(graph.metadata["connected_to_main_pipeline"])
        self.assertEqual(graph.metadata["status"], "experimental_sidecar")
        self.assertGreaterEqual(len(graph.entities), 3)
        self.assertTrue(any(relation.relation_type == "has_field:负责人" for relation in graph.relations))

    def test_export_graph_json_returns_valid_json(self) -> None:
        graph = KnowledgeGraphBuilder().from_text_units([
            {"id": "u1", "text": "第一段"},
            {"id": "u2", "text": "第二段"},
        ])

        payload = json.loads(export_graph_json(graph))

        self.assertEqual(payload["metadata"]["connected_to_main_pipeline"], False)
        self.assertEqual(len(payload["entities"]), 2)
        self.assertEqual(payload["relations"][0]["relation_type"], "next_text_unit")

    def test_persistent_graph_aggregates_cross_document_evidence(self) -> None:
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        db = sessionmaker(bind=engine)()
        try:
            user = User(id="u1", username="kg-user", email="kg@example.com", password_hash="x")
            organization = Organization(id="o1", name="知识图谱组织", slug="kg-org", owner_id=user.id)
            collection = KnowledgeCollection(id="k1", organization_id=organization.id, owner_id=user.id, name="项目知识库")
            documents = [
                DocumentRecord(id="d1", user_id=user.id, organization_id=organization.id, filename="立项书.txt", file_type="txt", storage_path="missing-1"),
                DocumentRecord(id="d2", user_id=user.id, organization_id=organization.id, filename="验收书.txt", file_type="txt", storage_path="missing-2"),
            ]
            items = [
                KnowledgeItem(id="i1", collection_id=collection.id, document_id="d1"),
                KnowledgeItem(id="i2", collection_id=collection.id, document_id="d2"),
            ]
            extractions = [
                ExtractionRecord(id="x1", user_id=user.id, organization_id=organization.id, document_id="d1", filename="立项书.txt", file_type="txt", fields_requested=["项目名称", "负责人"], extracted_data={"项目名称": "星河计划", "负责人": "林晓宇", "_meta": {"evidence": {"负责人": {"snippet": "项目负责人为林晓宇"}}, "confidence": {"负责人": 0.92}}}),
                ExtractionRecord(id="x2", user_id=user.id, organization_id=organization.id, document_id="d2", filename="验收书.txt", file_type="txt", fields_requested=["项目名称", "负责人"], extracted_data={"项目名称": "星河计划", "负责人": "林晓宇", "_meta": {"evidence": {"负责人": {"snippet": "林晓宇负责项目验收"}}, "confidence": {"负责人": 0.88}}}),
            ]
            db.add_all([user, organization, collection, *documents, *items, *extractions])
            db.commit()

            summary = rebuild_knowledge_graph(db, collection.id)
            db.commit()
            graph = serialize_knowledge_graph(db, collection.id)
            person = next(item for item in graph["entities"] if item["name"] == "林晓宇")
            context = graph_context_for_query(db, collection.id, "林晓宇负责哪个项目")

            self.assertEqual(summary["entity_count"], 4)
            self.assertEqual(set(person["source_ids"]), {"d1", "d2"})
            self.assertEqual(len(person["evidence"]), 2)
            self.assertIn("星河计划 —负责人→ 林晓宇", context["paths"])
            self.assertEqual(set(context["document_ids"]), {"d1", "d2"})

            stored_person = db.query(KnowledgeEntity).filter_by(id=person["entity_id"]).one()
            stored_person.review_status = "confirmed"
            db.commit()
            rebuild_knowledge_graph(db, collection.id)
            db.commit()
            rebuilt = serialize_knowledge_graph(db, collection.id)
            rebuilt_person = next(item for item in rebuilt["entities"] if item["name"] == "林晓宇")
            self.assertEqual(rebuilt_person["review_status"], "confirmed")
        finally:
            db.close()
            engine.dispose()


if __name__ == "__main__":
    unittest.main()
