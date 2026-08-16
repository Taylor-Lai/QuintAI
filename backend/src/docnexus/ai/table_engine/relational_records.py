"""Deterministic, template-anchored record construction.

The LLM extraction path is useful for prose, but spreadsheet-to-spreadsheet
tasks must not depend on a model rediscovering joins, units, and row identity.
This module builds high-confidence records from canonical tables and merges
them by the identity already present in the target template.
"""

from __future__ import annotations

import re
from collections import OrderedDict
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation

from docnexus.ai.table_engine.core.models import EvidencePack, StructuredRecord, TaskSpec

_PARENS_RE = re.compile(r"[（(][^）)]*[）)]")
_NON_WORD_RE = re.compile(r"[\s_\-—－:/：、，,。]+")
_QUARTER_SALES_RE = re.compile(
    r"(?P<region>[\u4e00-\u9fff]{2,8}区)\s*[：:]\s*"
    r"一季度\s*(?P<q1>-?\d+(?:\.\d+)?)\s*万元?\s*[，,]\s*"
    r"二季度\s*(?P<q2>-?\d+(?:\.\d+)?)\s*万元?"
)
_SIGNUP_RECORD_RE = re.compile(
    r"(?:报名信息\s*[：:]\s*)?"
    r"(?P<name>[\u4e00-\u9fff·]{2,20})\s*[，,]\s*"
    r"(?P<gender>男|女)\s*[，,]\s*"
    r"(?P<department>[^，,；;。]+?)\s*[，,]\s*"
    r"(?:手机(?:号)?|手机号|电话)\s*[：:]?\s*(?P<phone>1\d{10})"
)


def _norm(value: object) -> str:
    text = _PARENS_RE.sub("", str(value or "")).lower()
    text = _NON_WORD_RE.sub("", text)
    for suffix in ("分数", "得分", "分"):
        if text.endswith(suffix) and len(text) > len(suffix):
            text = text[: -len(suffix)]
            break
    return text


def _field_role(value: object) -> str:
    normalized = _norm(value)
    aliases = {
        "region": ("区域", "地区"),
        "month": ("月份", "年月", "month"),
        "project_id": ("项目编号", "项目id"),
        "credit_code": ("信用代码", "统一社会信用代码"),
        "q1": ("第一季度", "一季度", "q1"),
        "q2": ("第二季度", "二季度", "q2"),
        "income": ("净收入", "收入"),
        "cost": ("成本",),
        "budget": ("预算", "季度预算"),
        "quality": ("质量",),
        "delivery": ("交付",),
        "price": ("价格",),
        "service": ("服务",),
        "record_status": ("采用记录", "记录状态", "评审状态"),
        "sequence": ("序号", "编号"),
        "city": ("城市", "城市名"),
    }
    for role, names in aliases.items():
        if any(normalized == _norm(name) for name in names):
            return role
    return normalized


def _matches(source_field: str, target_field: str) -> bool:
    source_norm = _norm(source_field)
    target_norm = _norm(target_field)
    if not source_norm or not target_norm:
        return False
    if source_norm == target_norm or _field_role(source_field) == _field_role(target_field):
        return True
    if min(len(source_norm), len(target_norm)) >= 2 and (
        source_norm in target_norm or target_norm in source_norm
    ):
        # Refund and gross-income columns must never be treated as net income.
        if "退款" in source_norm or "退款" in target_norm:
            return source_norm == target_norm
        return True
    return False


def _as_decimal(value: object) -> Decimal | None:
    if value in (None, "") or isinstance(value, bool):
        return None
    try:
        return Decimal(str(value).replace(",", ""))
    except (InvalidOperation, ValueError):
        return None


def _number(value: Decimal) -> int | float:
    integral = value.to_integral_value()
    return int(integral) if value == integral else float(value)


def _convert_unit(source_field: str, target_field: str, value: object) -> object:
    number = _as_decimal(value)
    if number is None:
        return value
    source = str(source_field)
    target = str(target_field)
    if "（元）" in source or "(元)" in source:
        if "万元" in target:
            number /= Decimal("10000")
    return _number(number)


def _row_dict(table, row) -> dict[str, object]:
    result: dict[str, object] = {}
    for index, cell in enumerate(row.cells):
        header = table.headers[index].name if index < len(table.headers) else f"列{index + 1}"
        if header:
            result[str(header)] = cell.value
    return result


def _identity_fields(target_fields: list[str], template_values: list[dict[str, object]]) -> list[str]:
    roles = {_field_role(field_name): field_name for field_name in target_fields}
    if "month" in roles and "region" in roles:
        return [roles["month"], roles["region"]]
    for role in ("credit_code", "project_id", "region", "city"):
        if role in roles:
            return [roles[role]]
    for field_name in target_fields:
        if any(row.get(field_name) not in (None, "") for row in template_values):
            return [field_name]
    return [target_fields[0]] if target_fields else []


def _key(values: dict[str, object], identity_fields: list[str]) -> tuple[str, ...] | None:
    parts = tuple(_norm(values.get(field_name)) for field_name in identity_fields)
    return parts if parts and all(parts) else None


def _template_rows(template_doc, target_table, table_index: int) -> list[dict[str, object]]:
    if table_index >= len(template_doc.tables):
        return []
    table = template_doc.tables[table_index]
    header_index = target_table.anchor.row_index if target_table.anchor and target_table.anchor.row_index is not None else 0
    rows: list[dict[str, object]] = []
    fields = [field.field_name for field in target_table.schema]
    for row in table.rows[header_index + 1 :]:
        values = {
            field_name: row.cells[index].value if index < len(row.cells) else None
            for index, field_name in enumerate(fields)
        }
        if any(value not in (None, "") for value in values.values()):
            rows.append(values)
    return rows


def _evidence_id(evidence_pack: EvidencePack, source_doc_id: str, raw_row: dict[str, object], fallback: str) -> str:
    for item in evidence_pack.items:
        if item.source_doc_id != source_doc_id or item.evidence_type != "row" or not isinstance(item.content, dict):
            continue
        common = set(raw_row) & set(item.content)
        if common and all(str(raw_row[key]) == str(item.content[key]) for key in common):
            return item.evidence_id
    return fallback


@dataclass
class _Accumulator:
    values: dict[str, object]
    field_sources: dict[str, list[str]] = field(default_factory=dict)
    priority: int = 0
    notes: list[str] = field(default_factory=list)


def _source_priority(raw_row: dict[str, object]) -> int:
    status = "".join(str(value or "") for key, value in raw_row.items() if "状态" in str(key))
    if "终审" in status or "生效" in status:
        return 30
    if "初审" in status or "废弃" in status:
        return 5
    return 10


def _merge_value(acc: _Accumulator, field_name: str, value: object, evidence_id: str, *, aggregate: bool, priority: int) -> None:
    if value in (None, ""):
        return
    current = acc.values.get(field_name)
    if current in (None, ""):
        acc.values[field_name] = value
    elif aggregate:
        left, right = _as_decimal(current), _as_decimal(value)
        if left is not None and right is not None:
            acc.values[field_name] = _number(left + right)
        elif priority >= acc.priority:
            acc.values[field_name] = value
    elif priority >= acc.priority:
        acc.values[field_name] = value
    acc.field_sources.setdefault(field_name, [])
    if evidence_id not in acc.field_sources[field_name]:
        acc.field_sources[field_name].append(evidence_id)


def _paragraph_sales(source_docs, target_table) -> list[StructuredRecord]:
    target_fields = [field.field_name for field in target_table.schema]
    role_to_field = {_field_role(field_name): field_name for field_name in target_fields}
    if not {"region", "q1", "q2"}.issubset(role_to_field):
        return []
    records: list[StructuredRecord] = []
    for source_doc in source_docs:
        for block in source_doc.blocks:
            for match in _QUARTER_SALES_RE.finditer(block.text or ""):
                values = {field_name: None for field_name in target_fields}
                values[role_to_field["region"]] = match.group("region")
                values[role_to_field["q1"]] = float(match.group("q1"))
                values[role_to_field["q2"]] = float(match.group("q2"))
                sources = {key: [block.block_id] for key, value in values.items() if value not in (None, "")}
                records.append(StructuredRecord(
                    record_id=f"{target_table.target_table_id}#quarter-{len(records)}",
                    target_table_id=target_table.target_table_id,
                    values=values,
                    field_sources=sources,
                    confidence=0.98,
                    notes=["Deterministic quarter-sales extraction."],
                ))
    return records


def _paragraph_signup_records(source_docs, target_table) -> list[StructuredRecord]:
    """Extract repeated signup rows from common Chinese inline prose."""

    target_fields = [field.field_name for field in target_table.schema]

    def find_field(*tokens: str) -> str | None:
        return next(
            (field_name for field_name in target_fields if any(token in field_name for token in tokens)),
            None,
        )

    sequence_field = find_field("序号")
    name_field = find_field("姓名", "名字")
    gender_field = find_field("性别")
    department_field = find_field("部门")
    phone_field = find_field("手机号", "手机", "电话")
    if not all((sequence_field, name_field, gender_field, department_field, phone_field)):
        return []
    assert sequence_field is not None
    assert name_field is not None
    assert gender_field is not None
    assert department_field is not None
    assert phone_field is not None

    records: list[StructuredRecord] = []
    for source_doc in source_docs:
        for block in source_doc.blocks:
            for match in _SIGNUP_RECORD_RE.finditer(block.text or ""):
                values = {field_name: None for field_name in target_fields}
                values.update({
                    sequence_field: len(records) + 1,
                    name_field: match.group("name"),
                    gender_field: match.group("gender"),
                    department_field: match.group("department").strip(),
                    phone_field: match.group("phone"),
                })
                records.append(StructuredRecord(
                    record_id=f"{target_table.target_table_id}#signup-{len(records)}",
                    target_table_id=target_table.target_table_id,
                    values=values,
                    field_sources={
                        field_name: [block.block_id]
                        for field_name, value in values.items()
                        if value not in (None, "")
                    },
                    confidence=0.99,
                    notes=["Deterministic inline signup extraction."],
                ))
    return records


def _identity_value_in_text(value: str, text: str) -> bool:
    if value in text:
        return True
    month_match = re.fullmatch(r"\d{4}-(\d{2})", value)
    return bool(month_match and re.search(rf"(?<!\d)0?{int(month_match.group(1))}\s*月", text))


def _apply_text_overrides(accumulators, target_fields: list[str], identities: list[str], source_docs) -> None:
    note_field = next((field for field in target_fields if "备注" in field), None)
    conflict_field = next((field for field in target_fields if "冲突说明" in field), None)
    for source_doc in source_docs:
        for block in source_doc.blocks:
            text = block.text or ""
            if not text:
                continue
            for acc in accumulators.values():
                identity_values = [str(acc.values.get(field) or "") for field in identities]
                contexts = [
                    sentence.strip()
                    for sentence in re.split(r"[；;。\n]", text)
                    if sentence.strip() and all(value and _identity_value_in_text(value, sentence) for value in identity_values)
                ]
                if not identity_values or not contexts:
                    continue
                context = "；".join(contexts)
                for field_name in target_fields:
                    if field_name in context:
                        quoted = re.search(rf"{re.escape(field_name)}.*?[“\"]([^”\"]+)[”\"]", context)
                        if quoted:
                            acc.values[field_name] = quoted.group(1)
                            acc.field_sources[field_name] = [block.block_id]
                if note_field:
                    note_match = re.search(r"备注.*?[“\"]([^”\"]+)[”\"]", context)
                    if note_match:
                        acc.values[note_field] = note_match.group(1)
                        acc.field_sources[note_field] = [block.block_id]
                    elif "为准" in context:
                        basis = re.search(r"以(.+?)为准", context)
                        basis_text = re.sub(r"[“\"][^”\"]+[”\"]", "", basis.group(1)) if basis else ""
                        acc.values[note_field] = f"以{basis_text}为准" if basis_text else "以补充说明为准"
                        acc.field_sources[note_field] = [block.block_id]
                    elif "退款" in context:
                        amount = re.search(r"退款\s*(\d+(?:\.\d+)?)\s*万元", context)
                        acc.values[note_field] = f"扣除退款 {amount.group(1)} 万元" if amount else "已扣除退款"
                        acc.field_sources[note_field] = [block.block_id]
                    elif "重复" in context or "去重" in context:
                        acc.values[note_field] = "成本凭证去重"
                        acc.field_sources[note_field] = [block.block_id]
                if conflict_field and ("冲突" in context or ("以" in context and "为准" in context)):
                    acc.values[conflict_field] = "同一主键存在冲突，按终审或生效记录处理"
                    acc.field_sources[conflict_field] = [block.block_id]


def _build_exception_records(target_table, source_docs) -> list[StructuredRecord]:
    target_fields = [field.field_name for field in target_table.schema]
    required_labels = ("类型", "位置", "处理", "来源依据")
    if not all(any(label in field for field in target_fields) for label in required_labels):
        return []

    def field(label: str) -> str:
        return next(name for name in target_fields if label in name)

    sequence_field = next((name for name in target_fields if _field_role(name) == "sequence"), target_fields[0])
    rows: list[tuple[str, str, str, str, str]] = []
    seen_vouchers: dict[tuple[str, str], dict[str, object]] = {}
    version_groups: dict[str, list[tuple[dict[str, object], str]]] = {}
    for source_doc in source_docs:
        for table in source_doc.tables:
            for row in table.rows[1:]:
                raw = _row_dict(table, row)
                evidence = row.row_id
                region = next((str(value) for key, value in raw.items() if _field_role(key) == "region" and value), "")
                month = next((str(value) for key, value in raw.items() if _field_role(key) == "month" and value), "")
                refund_entry = next(((key, value) for key, value in raw.items() if "退款" in key and _as_decimal(value)), None)
                if refund_entry and region:
                    amount = _convert_unit(refund_entry[0], "退款（万元）", refund_entry[1])
                    voucher = next((str(value) for key, value in raw.items() if "凭证" in key and value), "")
                    rows.append(("退款调整", "/".join(value for value in (region, month) if value), f"收入扣减 {amount} 万元", f"补充说明与收入表 {voucher}".strip(), evidence))

                voucher = next((str(value) for key, value in raw.items() if "凭证" in key and value), "")
                if voucher:
                    voucher_key = (table.table_id, voucher)
                    if voucher_key in seen_vouchers:
                        rows.append(("重复记录", "/".join(value for value in (region, month) if value), f"成本凭证 {voucher} 仅计一次", "补充说明与成本表", evidence))
                    else:
                        seen_vouchers[voucher_key] = raw

                version = next((value for key, value in raw.items() if "版本" in key and value not in (None, "")), None)
                if region and version is not None:
                    version_groups.setdefault(region, []).append((raw, evidence))

    for region, versions in version_groups.items():
        if len(versions) < 2:
            continue
        active_raw, evidence = next(
            ((raw, evidence) for raw, evidence in versions if any("生效" in str(value) for value in raw.values())),
            versions[-1],
        )
        version = next(value for key, value in active_raw.items() if "版本" in key)
        budget = next((value for key, value in active_raw.items() if "预算" in key), None)
        rows.append(("版本选择", f"{region}预算", f"采用版本 {version}：{budget} 万元", "预算版本表生效状态", evidence))

    records: list[StructuredRecord] = []
    for index, (kind, location, handling, basis, evidence) in enumerate(rows, 1):
        values = {name: None for name in target_fields}
        values.update({
            sequence_field: index,
            field("类型"): kind,
            field("位置"): location,
            field("处理"): handling,
            field("来源依据"): basis,
        })
        records.append(StructuredRecord(
            record_id=f"{target_table.target_table_id}#exception-{index}",
            target_table_id=target_table.target_table_id,
            values=values,
            field_sources={name: [evidence] for name, value in values.items() if value not in (None, "")},
            confidence=0.99,
            notes=["Deterministic exception trace."],
        ))
    return records


def _task_request_text(task_spec: TaskSpec | None) -> str:
    if task_spec is None:
        return ""
    return "\n".join(
        str(constraint.value)
        for constraint in task_spec.constraints
        if constraint.kind == "request_text" and constraint.value
    )


def _excluded_identity_sentences(source_docs, request_text: str) -> list[str]:
    if "排除" not in request_text:
        return []
    terms = [term for term in ("取消资格", "废弃", "无效", "淘汰") if term in request_text]
    if not terms:
        return []
    return [
        sentence.strip()
        for source_doc in source_docs
        for block in source_doc.blocks
        for sentence in re.split(r"[。；;\n]", block.text or "")
        if sentence.strip() and any(term in sentence for term in terms)
    ]


def build_template_anchored_records(
    template_doc,
    source_docs,
    template_spec,
    evidence_pack: EvidencePack,
    task_spec: TaskSpec | None = None,
) -> list[StructuredRecord]:
    """Build and merge relational records without asking an LLM to infer joins."""

    output: list[StructuredRecord] = []
    request_text = _task_request_text(task_spec)
    excluded_sentences = _excluded_identity_sentences(source_docs, request_text)
    for table_index, target_table in enumerate(template_spec.target_tables):
        target_fields = [field.field_name for field in target_table.schema]
        exception_records = _build_exception_records(target_table, source_docs)
        if exception_records:
            output.extend(exception_records)
            continue
        template_rows = _template_rows(template_doc, target_table, table_index)
        identities = _identity_fields(target_fields, template_rows)
        accumulators: OrderedDict[tuple[str, ...], _Accumulator] = OrderedDict()

        for template_row in template_rows:
            identity = _key(template_row, identities)
            if identity:
                accumulators[identity] = _Accumulator(values=dict(template_row), notes=["Template identity preserved."])

        seen_vouchers: set[tuple[str, str]] = set()
        for source_doc in source_docs:
            for source_table in source_doc.tables:
                for source_row in source_table.rows[1:]:
                    raw_row = _row_dict(source_table, source_row)
                    if "排除" in request_text and any(
                        term in str(value)
                        for value in raw_row.values()
                        for term in ("取消资格", "废弃", "无效", "淘汰")
                        if term in request_text
                    ):
                        continue
                    voucher = next((str(value) for key, value in raw_row.items() if "凭证" in key and value not in (None, "")), "")
                    if voucher:
                        voucher_key = (source_table.table_id, voucher)
                        if voucher_key in seen_vouchers:
                            continue
                        seen_vouchers.add(voucher_key)

                    status_text = "".join(str(value or "") for key, value in raw_row.items() if "状态" in key)
                    if "废弃" in status_text or ("初审" in status_text and "终审" not in status_text):
                        # Keep initial-review rows only when no final row exists; the
                        # later high-priority row will recreate the same identity.
                        priority = 5
                    else:
                        priority = _source_priority(raw_row)

                    mapped: dict[str, object] = {field_name: None for field_name in target_fields}
                    mapped_sources: dict[str, str] = {}
                    evidence_id = _evidence_id(evidence_pack, source_doc.doc_id, raw_row, source_row.row_id)
                    for source_field, source_value in raw_row.items():
                        for target_field in target_fields:
                            if _matches(source_field, target_field):
                                value = _convert_unit(source_field, target_field, source_value)
                                if _field_role(target_field) == "income" and "收入" in source_field:
                                    refund = next((v for k, v in raw_row.items() if "退款" in k), 0)
                                    refund_value = _convert_unit(next((k for k in raw_row if "退款" in k), ""), target_field, refund)
                                    income_number, refund_number = _as_decimal(value), _as_decimal(refund_value)
                                    if income_number is not None and refund_number is not None:
                                        value = _number(income_number - refund_number)
                                mapped[target_field] = value
                                mapped_sources[target_field] = evidence_id
                                break

                    note_field = next((name for name in target_fields if "备注" in name), None)
                    if note_field:
                        refund_entry = next(
                            ((name, value) for name, value in raw_row.items() if "退款" in name and _as_decimal(value)),
                            None,
                        )
                        if refund_entry:
                            amount = _convert_unit(refund_entry[0], "退款（万元）", refund_entry[1])
                            mapped[note_field] = f"扣除退款 {amount} 万元"
                            mapped_sources[note_field] = evidence_id

                    identity = _key(mapped, identities)
                    if identity is None:
                        continue
                    acc = accumulators.setdefault(identity, _Accumulator(values={field_name: None for field_name in target_fields}))
                    conflict_field = next((name for name in target_fields if "冲突说明" in name), None)
                    if conflict_field and any(
                        acc.values.get(name) not in (None, "", value)
                        for name, value in mapped.items()
                        if value not in (None, "")
                    ):
                        supplier_field = next((name for name in target_fields if "供应商" in name), None)
                        supplier_changed = bool(
                            supplier_field
                            and mapped.get(supplier_field) not in (None, "")
                            and acc.values.get(supplier_field) not in (None, "", mapped.get(supplier_field))
                        )
                        acc.values[conflict_field] = (
                            "名称与初审记录不同，以信用代码去重并采用终审"
                            if supplier_changed and "终审" in status_text
                            else "同一主键存在冲突，按终审或生效记录处理"
                        )
                        acc.field_sources[conflict_field] = [evidence_id]
                    aggregate_roles = {"income", "cost"} if set(_field_role(field_name) for field_name in identities) <= {"region"} else set()
                    for field_name, value in mapped.items():
                        _merge_value(
                            acc,
                            field_name,
                            value,
                            mapped_sources.get(field_name, evidence_id),
                            aggregate=_field_role(field_name) in aggregate_roles,
                            priority=priority,
                        )
                    acc.priority = max(acc.priority, priority)
                    acc.notes.append(f"Merged canonical row from {source_doc.file.name}/{source_table.name}.")

        _apply_text_overrides(accumulators, target_fields, identities, source_docs)
        if excluded_sentences:
            accumulators = OrderedDict(
                (identity, accumulator)
                for identity, accumulator in accumulators.items()
                if not any(
                    all(value and _identity_value_in_text(value, sentence) for value in identity)
                    for sentence in excluded_sentences
                )
            )

        for signup_record in _paragraph_signup_records(source_docs, target_table):
            identity = _key(signup_record.values, identities)
            if identity is None:
                continue
            acc = accumulators.setdefault(identity, _Accumulator(values={field_name: None for field_name in target_fields}))
            for field_name, value in signup_record.values.items():
                if value not in (None, ""):
                    acc.values[field_name] = value
                    acc.field_sources[field_name] = list(signup_record.field_sources.get(field_name, []))
            acc.priority = max(acc.priority, 40)
            acc.notes.extend(signup_record.notes)

        for sales_record in _paragraph_sales(source_docs, target_table):
            identity = _key(sales_record.values, identities)
            if identity is None:
                continue
            acc = accumulators.setdefault(identity, _Accumulator(values={field_name: None for field_name in target_fields}))
            for field_name, value in sales_record.values.items():
                if value not in (None, ""):
                    acc.values[field_name] = value
                    acc.field_sources[field_name] = list(sales_record.field_sources.get(field_name, []))
            acc.priority = max(acc.priority, 40)
            acc.notes.extend(sales_record.notes)

        for record_index, acc in enumerate(accumulators.values()):
            non_identity_values = [value for field_name, value in acc.values.items() if field_name not in identities]
            if not any(value not in (None, "") for value in non_identity_values):
                continue
            output.append(StructuredRecord(
                record_id=f"{target_table.target_table_id}#relational-{record_index}",
                target_table_id=target_table.target_table_id,
                values=acc.values,
                field_sources=acc.field_sources,
                confidence=0.98,
                status="ready",
                notes=list(dict.fromkeys(acc.notes)),
            ))
    return output
