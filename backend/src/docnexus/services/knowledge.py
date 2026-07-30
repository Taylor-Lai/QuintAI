"""Local, deterministic hybrid retrieval with auditable document citations."""

from __future__ import annotations

import hashlib
import math
import re
import uuid
from collections import Counter
from pathlib import Path

from sqlalchemy.orm import Session

from docnexus.db import DocumentRecord, KnowledgeChunk
from docnexus.services.document_parser import DocumentParser

VECTOR_SIZE = 256


def _tokens(text: str) -> list[str]:
    normalized = re.sub(r"\s+", "", text.lower())
    chinese = re.findall(r"[\u4e00-\u9fff]", normalized)
    bigrams = ["".join(chinese[index : index + 2]) for index in range(max(0, len(chinese) - 1))]
    words = re.findall(r"[a-z0-9_.%-]+", normalized)
    return [*chinese, *bigrams, *words]


def embed_text(text: str) -> list[float]:
    """Feature-hashed lexical vector; deterministic, offline and suitable for cosine retrieval."""
    vector = [0.0] * VECTOR_SIZE
    for token, count in Counter(_tokens(text)).items():
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % VECTOR_SIZE
        sign = 1 if digest[4] % 2 == 0 else -1
        vector[index] += sign * (1 + math.log(count))
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [round(value / norm, 6) for value in vector]


def _cosine(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right, strict=False))


def _read_document(path: Path) -> str:
    content = path.read_bytes()
    suffix = path.suffix.lower()
    if suffix == ".docx":
        return DocumentParser._parse_docx(content)
    if suffix == ".xlsx":
        return DocumentParser._parse_xlsx(content)
    if suffix in {".txt", ".md"}:
        return DocumentParser._parse_text(content)
    return ""


def split_chunks(text: str, target_size: int = 650, overlap: int = 100) -> list[str]:
    paragraphs = [part.strip() for part in re.split(r"\n+", text) if part.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if current and len(current) + len(paragraph) + 1 > target_size:
            chunks.append(current)
            current = current[-overlap:] + "\n" + paragraph
        else:
            current = f"{current}\n{paragraph}".strip()
    if current:
        chunks.append(current)
    return chunks or ([text[:target_size]] if text else [])


def index_document(db: Session, collection_id: str, document: DocumentRecord) -> int:
    path = Path(document.storage_path)
    text = _read_document(path) if path.is_file() else document.content_preview or ""
    chunks = split_chunks(text)
    db.query(KnowledgeChunk).filter_by(collection_id=collection_id, document_id=document.id).delete()
    for index, content in enumerate(chunks):
        db.add(
            KnowledgeChunk(
                id=uuid.uuid4().hex,
                collection_id=collection_id,
                document_id=document.id,
                chunk_index=index,
                content=content,
                location={"chunk_index": index, "character_start": max(0, index * 550)},
                embedding=embed_text(content),
            )
        )
    return len(chunks)


def hybrid_search(
    db: Session,
    collection_id: str,
    query: str,
    mode: str,
    limit: int,
    *,
    graph_context: dict | None = None,
) -> list[dict]:
    query_tokens = set(_tokens(query))
    query_vector = embed_text(query)
    rows = db.query(KnowledgeChunk).filter_by(collection_id=collection_id).all()
    document_ids = {row.document_id for row in rows}
    documents = {
        row.id: row for row in db.query(DocumentRecord).filter(DocumentRecord.id.in_(document_ids)).all()
    } if document_ids else {}
    results: list[dict] = []
    for row in rows:
        chunk_tokens = _tokens(row.content)
        counts = Counter(chunk_tokens)
        keyword = sum(counts[token] for token in query_tokens) / max(1, len(chunk_tokens))
        vector = max(0.0, _cosine(query_vector, list(row.embedding or [])))
        if mode == "keyword":
            score = keyword
        elif mode == "vector":
            score = vector
        else:
            score = keyword * 0.45 + vector * 0.55
        graph_document_ids = set((graph_context or {}).get("document_ids") or [])
        graph_bonus = 0.12 if row.document_id in graph_document_ids else 0.0
        score = min(1.0, score + graph_bonus)
        if score <= 0:
            continue
        document = documents.get(row.document_id)
        results.append(
            {
                "chunk_id": row.id,
                "document_id": row.document_id,
                "filename": document.filename if document else "未知文档",
                "score": round(score, 6),
                "keyword_score": round(keyword, 6),
                "vector_score": round(vector, 6),
                "graph_score": graph_bonus,
                "graph_paths": list((graph_context or {}).get("paths") or [])[:3] if graph_bonus else [],
                "snippet": row.content[:500],
                "citation": {**(row.location or {}), "document_id": row.document_id, "filename": document.filename if document else "未知文档"},
            }
        )
    results.sort(key=lambda item: item["score"], reverse=True)
    return results[:limit]
