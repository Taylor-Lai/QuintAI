"""Build independent source datasets from row-level evidence."""

from __future__ import annotations

from pathlib import Path

from docnexus.ai.table_engine.core.models import CanonicalDocument, EvidencePack, StructuredRecord


def build_source_datasets(
    evidence_pack: EvidencePack,
    source_docs: list[CanonicalDocument],
    *,
    target_table_id: str,
) -> dict[str, list[StructuredRecord]]:
    """Return datasets addressable by document id, filename, stem, and the aggregate 'source' alias."""
    by_doc: dict[str, list[StructuredRecord]] = {document.doc_id: [] for document in source_docs}
    all_records: list[StructuredRecord] = []
    for item in evidence_pack.items:
        if item.evidence_type != "row" or not isinstance(item.content, dict):
            continue
        values = dict(item.content)
        record = StructuredRecord(
            record_id=f"source:{item.evidence_id}",
            target_table_id=target_table_id,
            values=values,
            field_sources={field_name: [item.evidence_id] for field_name, value in values.items() if value not in (None, "")},
            confidence=item.score,
            notes=[f"Built from source dataset {item.source_doc_id}."],
        )
        by_doc.setdefault(item.source_doc_id, []).append(record)
        all_records.append(record)

    datasets: dict[str, list[StructuredRecord]] = {"source": all_records}
    for document in source_docs:
        records = by_doc.get(document.doc_id, [])
        aliases = {
            document.doc_id,
            document.file.name,
            Path(document.file.name).stem,
            str(document.metadata.get("logical_name") or ""),
        }
        for alias in aliases:
            if alias:
                datasets[alias] = records
    return datasets
