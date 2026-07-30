"""Persistent, evidence-backed knowledge graph construction and querying."""

from __future__ import annotations

import hashlib
import re
import uuid
from collections import Counter, defaultdict
from typing import Any, Iterable

from sqlalchemy import or_
from sqlalchemy.orm import Session

from docnexus.db import (
    DocumentRecord,
    ExtractionRecord,
    KnowledgeChunk,
    KnowledgeEntity,
    KnowledgeEvidence,
    KnowledgeItem,
    KnowledgeRelation,
)

ENTITY_TYPE_HINTS = {
    "人员": ("负责人", "姓名", "联系人", "教师", "作者", "经理", "成员"),
    "组织": ("单位", "学校", "公司", "机构", "部门", "团队", "供应商"),
    "地点": ("地址", "地点", "城市", "省份", "国家", "区域"),
    "时间": ("日期", "时间", "年份", "月份", "周期", "期限"),
    "指标": ("金额", "预算", "数量", "人口", "gdp", "收入", "病例", "检测", "比例", "率", "指标"),
    "项目": ("项目", "课题", "任务", "工程", "计划"),
}


def _stable_id(prefix: str, *parts: object) -> str:
    digest = hashlib.sha256("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()[:24]
    return f"{prefix}{digest}"[:32]


def normalize_entity_name(value: object) -> str:
    return re.sub(r"[\s\u3000]+", "", str(value)).strip().casefold()


def infer_entity_type(field_name: str, value: object) -> str:
    name = field_name.casefold()
    for entity_type, tokens in ENTITY_TYPE_HINTS.items():
        if any(token.casefold() in name for token in tokens):
            return entity_type
    text = str(value)
    if re.search(r"\d{4}[年/-]\d{1,2}", text):
        return "时间"
    if re.search(r"\d", text):
        return "指标"
    return "概念"


def relation_type_for(field_name: str, entity_type: str) -> str:
    if any(token in field_name for token in ("负责人", "联系人", "经理")):
        return "负责人"
    if any(token in field_name for token in ("所属", "隶属", "单位", "机构", "公司")):
        return "隶属机构"
    return {
        "地点": "位于",
        "时间": "发生于",
        "指标": "具有指标",
        "人员": "关联人员",
        "组织": "关联组织",
    }.get(entity_type, "关联")


def _field_values(value: object) -> Iterable[object]:
    if isinstance(value, list):
        yield from (item for item in value if item not in (None, "", "未找到"))
    elif isinstance(value, dict) and "value" in value:
        yield from _field_values(value.get("value"))
    elif value not in (None, "", "未找到"):
        yield value


def _metadata(extraction: ExtractionRecord) -> dict[str, Any]:
    data = extraction.extracted_data or {}
    meta = data.get("_meta")
    return meta if isinstance(meta, dict) else {}


def _confidence(extraction: ExtractionRecord, field_name: str) -> float:
    values = _metadata(extraction).get("confidence")
    value = values.get(field_name, 0.7) if isinstance(values, dict) else 0.7
    try:
        return max(0.0, min(float(value), 1.0))
    except (TypeError, ValueError):
        return 0.7


def _evidence_data(extraction: ExtractionRecord, field_name: str) -> dict[str, Any]:
    values = _metadata(extraction).get("evidence")
    item = values.get(field_name) if isinstance(values, dict) else None
    return item if isinstance(item, dict) else {}


def rebuild_knowledge_graph(db: Session, collection_id: str) -> dict[str, int]:
    """Rebuild one collection atomically from authorized source records."""
    document_ids = [
        row[0] for row in db.query(KnowledgeItem.document_id).filter_by(collection_id=collection_id).all()
    ]
    existing_entities = db.query(KnowledgeEntity).filter_by(collection_id=collection_id).all()
    review_state = {
        (row.entity_type, row.normalized_name): (row.review_status, list(row.aliases or []))
        for row in existing_entities
    }
    db.query(KnowledgeEvidence).filter_by(collection_id=collection_id).delete(synchronize_session=False)
    db.query(KnowledgeRelation).filter_by(collection_id=collection_id).delete(synchronize_session=False)
    db.query(KnowledgeEntity).filter_by(collection_id=collection_id).delete(synchronize_session="fetch")
    db.flush()
    if not document_ids:
        return {"entity_count": 0, "relation_count": 0, "evidence_count": 0}

    documents = {
        item.id: item for item in db.query(DocumentRecord).filter(DocumentRecord.id.in_(document_ids)).all()
    }
    chunks = db.query(KnowledgeChunk).filter_by(collection_id=collection_id).all()
    chunks_by_document_index = {(row.document_id, row.chunk_index): row for row in chunks}
    entities: dict[tuple[str, str], KnowledgeEntity] = {}
    relations: dict[tuple[str, str, str], KnowledgeRelation] = {}
    evidence_keys: set[tuple[str | None, str | None, str, str | None, str | None]] = set()

    def entity(
        entity_type: str,
        name: object,
        *,
        identity: object | None = None,
        attributes: dict[str, Any] | None = None,
        confidence: float = 0.7,
    ) -> KnowledgeEntity:
        canonical_name = re.sub(r"\s+", " ", str(name)).strip()
        normalized = normalize_entity_name(identity if identity is not None else canonical_name)
        key = (entity_type, normalized)
        row = entities.get(key)
        if row is None:
            previous_status, previous_aliases = review_state.get((entity_type, normalized), ("unreviewed", []))
            row = KnowledgeEntity(
                id=_stable_id("e", collection_id, entity_type, normalized),
                collection_id=collection_id,
                entity_type=entity_type,
                canonical_name=canonical_name[:255],
                normalized_name=normalized[:255],
                aliases=previous_aliases,
                attributes=attributes or {},
                confidence=confidence,
                review_status=previous_status,
            )
            entities[key] = row
            db.add(row)
        else:
            row.confidence = max(row.confidence, confidence)
            row.attributes = {**(row.attributes or {}), **(attributes or {})}
            if canonical_name != row.canonical_name and canonical_name not in (row.aliases or []):
                row.aliases = [*(row.aliases or []), canonical_name]
        return row

    def relation(source: KnowledgeEntity, target: KnowledgeEntity, relation_type: str, confidence: float) -> KnowledgeRelation:
        key = (source.id, target.id, relation_type)
        row = relations.get(key)
        if row is None:
            row = KnowledgeRelation(
                id=_stable_id("r", collection_id, *key), collection_id=collection_id,
                source_entity_id=source.id, target_entity_id=target.id,
                relation_type=relation_type, confidence=confidence, attributes={},
            )
            relations[key] = row
            db.add(row)
        else:
            row.confidence = max(row.confidence, confidence)
        return row

    def add_evidence(*, target_entity: KnowledgeEntity | None, target_relation: KnowledgeRelation | None,
                     document_id: str, extraction: ExtractionRecord | None = None,
                     field_name: str | None = None, evidence: dict[str, Any] | None = None,
                     fallback: str = "", confidence: float = 0.7) -> None:
        evidence = evidence or {}
        chunk_index = evidence.get("chunk_id")
        chunk = chunks_by_document_index.get((document_id, chunk_index)) if isinstance(chunk_index, int) else None
        key = (target_entity.id if target_entity else None, target_relation.id if target_relation else None,
               document_id, extraction.id if extraction else None, field_name)
        if key in evidence_keys:
            return
        evidence_keys.add(key)
        db.add(KnowledgeEvidence(
            id=uuid.uuid4().hex, collection_id=collection_id,
            entity_id=target_entity.id if target_entity else None,
            relation_id=target_relation.id if target_relation else None,
            document_id=document_id, chunk_id=chunk.id if chunk else None,
            extraction_id=extraction.id if extraction else None, field_name=field_name,
            snippet=str(evidence.get("snippet") or fallback)[:2000],
            location={"chunk_index": chunk_index, "char_range": evidence.get("char_range"), **(chunk.location if chunk else {})},
            confidence=confidence,
        ))

    document_entities: dict[str, KnowledgeEntity] = {}
    for document in documents.values():
        row = entity(
            "文档", document.filename, identity=f"{document.filename}#{document.id}",
            attributes={"document_id": document.id, "file_type": document.file_type, "category": document.category},
            confidence=1.0,
        )
        document_entities[document.id] = row
        add_evidence(target_entity=row, target_relation=None, document_id=document.id, fallback=document.content_preview, confidence=1.0)

    extractions = db.query(ExtractionRecord).filter(ExtractionRecord.document_id.in_(document_ids)).all()
    for extraction in extractions:
        if not extraction.document_id or extraction.document_id not in document_entities:
            continue
        document_entity = document_entities[extraction.document_id]
        extracted_entities: list[tuple[str, KnowledgeEntity, str, float, dict[str, Any]]] = []
        for field_name, raw_value in (extraction.extracted_data or {}).items():
            if str(field_name).startswith("_"):
                continue
            for value in _field_values(raw_value):
                confidence = _confidence(extraction, str(field_name))
                entity_type = infer_entity_type(str(field_name), value)
                value_entity = entity(entity_type, value, attributes={"field_names": [str(field_name)]}, confidence=confidence)
                if str(field_name) not in value_entity.attributes.get("field_names", []):
                    value_entity.attributes = {**value_entity.attributes, "field_names": [*value_entity.attributes.get("field_names", []), str(field_name)]}
                evidence = _evidence_data(extraction, str(field_name))
                document_relation = relation(document_entity, value_entity, "记载", confidence)
                add_evidence(target_entity=value_entity, target_relation=None, document_id=extraction.document_id,
                             extraction=extraction, field_name=str(field_name), evidence=evidence,
                             fallback=f"{field_name}：{value}", confidence=confidence)
                add_evidence(target_entity=None, target_relation=document_relation, document_id=extraction.document_id,
                             extraction=extraction, field_name=str(field_name), evidence=evidence,
                             fallback=f"{field_name}：{value}", confidence=confidence)
                extracted_entities.append((str(field_name), value_entity, entity_type, confidence, evidence))

        subjects = [item for item in extracted_entities if item[2] == "项目"]
        if subjects:
            subject = subjects[0][1]
            for field_name, target, entity_type, confidence, evidence in extracted_entities:
                if target.id == subject.id:
                    continue
                semantic_relation = relation(subject, target, relation_type_for(field_name, entity_type), confidence)
                add_evidence(target_entity=None, target_relation=semantic_relation, document_id=extraction.document_id,
                             extraction=extraction, field_name=field_name, evidence=evidence,
                             fallback=f"{field_name}：{target.canonical_name}", confidence=confidence)

    db.flush()
    return {"entity_count": len(entities), "relation_count": len(relations), "evidence_count": len(evidence_keys)}


def serialize_knowledge_graph(db: Session, collection_id: str) -> dict[str, Any]:
    entities = db.query(KnowledgeEntity).filter_by(collection_id=collection_id).all()
    relations = db.query(KnowledgeRelation).filter_by(collection_id=collection_id).all()
    evidence = db.query(KnowledgeEvidence).filter_by(collection_id=collection_id).all()
    documents = {
        row.id: row for row in db.query(DocumentRecord).filter(
            DocumentRecord.id.in_({item.document_id for item in evidence})
        ).all()
    } if evidence else {}
    by_entity: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_relation: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in evidence:
        document = documents.get(item.document_id)
        payload = {
            "id": item.id, "document_id": item.document_id,
            "filename": document.filename if document else "未知文档",
            "chunk_id": item.chunk_id, "extraction_id": item.extraction_id,
            "field_name": item.field_name, "snippet": item.snippet,
            "location": item.location or {}, "confidence": item.confidence,
        }
        if item.entity_id:
            by_entity[item.entity_id].append(payload)
        if item.relation_id:
            by_relation[item.relation_id].append(payload)
    type_counts = Counter(item.entity_type for item in entities)
    return {
        "collection_id": collection_id,
        "entities": [
            {
                "entity_id": item.id, "entity_type": item.entity_type,
                "name": item.canonical_name, "aliases": item.aliases or [],
                "attributes": item.attributes or {}, "confidence": item.confidence,
                "review_status": item.review_status,
                "source_ids": sorted({source["document_id"] for source in by_entity[item.id]}),
                "evidence": by_entity[item.id],
            }
            for item in entities
        ],
        "relations": [
            {
                "relation_id": item.id, "source_entity_id": item.source_entity_id,
                "target_entity_id": item.target_entity_id, "relation_type": item.relation_type,
                "confidence": item.confidence, "attributes": item.attributes or {},
                "source_ids": sorted({source["document_id"] for source in by_relation[item.id]}),
                "evidence": by_relation[item.id],
            }
            for item in relations
        ],
        "metadata": {
            "status": "persistent_evidence_graph", "connected_to_main_pipeline": True,
            "entity_count": len(entities), "relation_count": len(relations), "evidence_count": len(evidence),
            "entity_types": dict(type_counts),
        },
    }


def graph_context_for_query(db: Session, collection_id: str, query: str, *, limit: int = 8) -> dict[str, Any]:
    normalized_query = normalize_entity_name(query)
    terms = {normalize_entity_name(term) for term in re.findall(r"[\u4e00-\u9fff]{2,}|[a-zA-Z0-9_.%-]+", query)}
    entities = db.query(KnowledgeEntity).filter_by(collection_id=collection_id).all()
    matched = [
        item for item in entities
        if item.normalized_name in normalized_query
        or normalized_query in item.normalized_name
        or any(term and (term in item.normalized_name or item.normalized_name in term) for term in terms)
    ][:limit]
    if not matched:
        return {"entities": [], "relations": [], "document_ids": [], "paths": []}
    matched_ids = {item.id for item in matched}
    relations = db.query(KnowledgeRelation).filter(
        KnowledgeRelation.collection_id == collection_id,
        or_(KnowledgeRelation.source_entity_id.in_(matched_ids), KnowledgeRelation.target_entity_id.in_(matched_ids)),
    ).limit(limit * 3).all()
    expanded_ids = matched_ids | {item.source_entity_id for item in relations} | {item.target_entity_id for item in relations}
    expanded = {item.id: item for item in db.query(KnowledgeEntity).filter(KnowledgeEntity.id.in_(expanded_ids)).all()}
    evidence = db.query(KnowledgeEvidence).filter(
        KnowledgeEvidence.collection_id == collection_id,
        or_(KnowledgeEvidence.entity_id.in_(expanded_ids), KnowledgeEvidence.relation_id.in_([item.id for item in relations])),
    ).all()
    document_ids = sorted({item.document_id for item in evidence})
    return {
        "entities": [{"entity_id": item.id, "name": item.canonical_name, "entity_type": item.entity_type} for item in matched],
        "relations": [{"relation_id": item.id, "source": expanded[item.source_entity_id].canonical_name,
                       "relation_type": item.relation_type, "target": expanded[item.target_entity_id].canonical_name,
                       "confidence": item.confidence} for item in relations if item.source_entity_id in expanded and item.target_entity_id in expanded],
        "document_ids": document_ids,
        "paths": [f"{expanded[item.source_entity_id].canonical_name} —{item.relation_type}→ {expanded[item.target_entity_id].canonical_name}"
                  for item in relations if item.source_entity_id in expanded and item.target_entity_id in expanded],
    }
