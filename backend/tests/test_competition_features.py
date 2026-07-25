"""Deterministic tests for progress, quality, retrieval and scheduling features."""

from datetime import datetime, timezone

from docnexus.db import (
    Base,
    DocumentRecord,
    KnowledgeCollection,
    Organization,
    TaskRecord,
    User,
)
from docnexus.services import task_progress
from docnexus.services.knowledge import hybrid_search, index_document
from docnexus.services.quality import extraction_quality, safely_repair_fields
from docnexus.services.scheduling import cron_matches, next_cron_time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def _session(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'features.db'}")
    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine)()


def test_safe_repair_and_quality_are_explainable() -> None:
    fields = [
        {"name": "金额", "value": " 1,280 ", "confidence": 0.95, "evidence": "金额 1,280 元"},
        {"name": "负责人", "value": "", "confidence": 0.4, "evidence": ""},
    ]
    repaired, changes = safely_repair_fields(fields)
    quality = extraction_quality(repaired, [{"level": "warning"}])

    assert repaired[0]["value"] == "1280"
    assert repaired[0]["original_value"] == " 1,280 "
    assert changes == [{"field": "金额", "before": " 1,280 ", "after": "1280"}]
    assert quality["completeness"] == 0.5
    assert quality["evidence_coverage"] == 0.5
    assert quality["requires_review"] is True


def test_hybrid_search_indexes_real_source_and_returns_citation(tmp_path) -> None:
    engine, db = _session(tmp_path)
    try:
        source = tmp_path / "项目说明.txt"
        source.write_text("星河项目负责人是林晓宇，预算为六十八万元。\n验收要求是字段准确率不低于百分之九十二。", encoding="utf-8")
        user = User(id="u1", username="tester", email="tester@example.com", password_hash="x")
        org = Organization(id="o1", name="测试组织", slug="test-org", owner_id=user.id)
        document = DocumentRecord(
            id="d1",
            user_id=user.id,
            organization_id=org.id,
            filename=source.name,
            file_type="txt",
            size_bytes=source.stat().st_size,
            storage_path=str(source),
        )
        collection = KnowledgeCollection(id="k1", organization_id=org.id, owner_id=user.id, name="项目库")
        db.add_all([user, org, document, collection])
        db.commit()

        assert index_document(db, collection.id, document) == 1
        db.commit()
        results = hybrid_search(db, collection.id, "项目负责人", "hybrid", 5)

        assert results[0]["filename"] == source.name
        assert results[0]["citation"]["document_id"] == document.id
        assert "林晓宇" in results[0]["snippet"]
        assert results[0]["vector_score"] > 0
    finally:
        db.close()
        engine.dispose()


def test_cron_supports_ranges_steps_and_timezones() -> None:
    assert cron_matches("*/15 9-18 * * 1-5", datetime(2026, 7, 27, 9, 30))
    assert not cron_matches("*/15 9-18 * * 1-5", datetime(2026, 7, 26, 9, 30))
    result = next_cron_time("0 9 * * 1-5", "Asia/Shanghai", datetime(2026, 7, 24, 18, 0, tzinfo=timezone.utc))
    assert result == datetime(2026, 7, 27, 1, 0)


def test_progress_is_derived_from_persisted_completed_steps(tmp_path, monkeypatch) -> None:
    engine, db = _session(tmp_path)
    factory = sessionmaker(bind=engine)
    monkeypatch.setattr(task_progress, "SessionLocal", factory)
    try:
        user = User(id="u2", username="runner", email="runner@example.com", password_hash="x")
        task = TaskRecord(
            id="t1",
            celery_task_id="celery-1",
            user_id=user.id,
            kind="document_extract",
            payload={},
            status="running",
            total_steps=5,
        )
        db.add_all([user, task])
        db.commit()

        task_progress.report_step(task.id, "extract", "提取字段", "running", 1, 5)
        task_progress.report_step(task.id, "extract", "提取字段", "completed", 2, 5)
        db.expire_all()
        updated = db.get(TaskRecord, task.id)
        events = task_progress.serialize_events(task.id)

        assert updated.progress == 40
        assert updated.completed_steps == 2
        assert len(events) == 1
        assert events[0]["status"] == "completed"
        assert events[0]["progress"] == 40
    finally:
        db.close()
        engine.dispose()
