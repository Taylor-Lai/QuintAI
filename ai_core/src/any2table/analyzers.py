"""Template analyzers."""

from __future__ import annotations

import re

from any2table.core.models import CanonicalDocument, Constraint, FieldSpec, LocationRef, TargetTableSpec, TemplateSpec

ISO_DATETIME_PATTERN = re.compile(r"(\d{4}-\d{1,2}-\d{1,2}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?)")
CN_DATETIME_PATTERN = re.compile(r"(\d{4})年(\d{1,2})月(\d{1,2})日(\d{2}:\d{2})")
CITY_WITH_CONTEXT_PATTERN = re.compile(r"([\u4e00-\u9fff]{2,10}?市)(?:各|环境|空气|区域|监测)")
CITY_PATTERN = re.compile(r"([\u4e00-\u9fff]{2,10}?市)")
CITY_PREFIXES = ("时刻", "记录", "关于", "本表")
HEADER_SCAN_LIMIT = 5


def _extract_exact_datetime(description: str) -> str | None:
    iso_match = ISO_DATETIME_PATTERN.search(description)
    if iso_match:
        return iso_match.group(1)

    cn_match = CN_DATETIME_PATTERN.search(description)
    if not cn_match:
        return None

    year, month, day, hm = cn_match.groups()
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d} {hm}:00.0"


def _clean_city_candidate(city: str) -> str:
    cleaned = city
    changed = True
    while changed:
        changed = False
        for prefix in CITY_PREFIXES:
            if cleaned.startswith(prefix) and len(cleaned) > len(prefix):
                cleaned = cleaned[len(prefix):]
                changed = True
    return cleaned


def _extract_city(description: str) -> str | None:
    contextual_match = CITY_WITH_CONTEXT_PATTERN.search(description)
    if contextual_match:
        return _clean_city_candidate(contextual_match.group(1))

    city_match = CITY_PATTERN.search(description)
    if city_match:
        return _clean_city_candidate(city_match.group(1))
    return None


def _extract_local_constraints(table_id: str, description: str | None) -> list[Constraint]:
    if not description:
        return []

    constraints: list[Constraint] = []
    city = _extract_city(description)
    if city:
        constraints.append(
            Constraint(
                constraint_id=f"{table_id}#city",
                source="template_description",
                kind="entity",
                field="城市",
                operator="equals",
                value=city,
            )
        )

    exact_datetime = _extract_exact_datetime(description)
    if exact_datetime:
        constraints.append(
            Constraint(
                constraint_id=f"{table_id}#datetime",
                source="template_description",
                kind="exact_datetime",
                field="监测时间",
                operator="equals",
                value=exact_datetime,
            )
        )

    return constraints


def _cell_text(value: object) -> str:
    return "" if value is None else str(value).strip()


def _row_values(table, row_index: int) -> list[str]:
    if row_index < 0 or row_index >= len(table.rows):
        return []
    return [_cell_text(cell.value) for cell in table.rows[row_index].cells]


def _non_empty_count(values: list[str]) -> int:
    return sum(1 for value in values if value)


def _select_header_row_index(table) -> int:
    if not table.rows:
        return 0
    best_index = 0
    best_score = -1
    scan_count = min(len(table.rows), HEADER_SCAN_LIMIT)
    for row_index in range(scan_count):
        values = _row_values(table, row_index)
        non_empty = _non_empty_count(values)
        unique_count = len({value for value in values if value})
        numeric_count = sum(1 for value in values if re.fullmatch(r"-?\d+(?:\.\d+)?", value))
        score = non_empty * 3 + unique_count - numeric_count * 2
        if non_empty <= 1 and row_index + 1 < scan_count:
            score -= 4
        if score > best_score:
            best_score = score
            best_index = row_index
    return best_index


def _compose_header_names(table, header_row_index: int) -> list[str]:
    current = _row_values(table, header_row_index)
    previous = _row_values(table, header_row_index - 1)
    max_len = max(len(current), len(previous), len(table.headers))
    names: list[str] = []
    for col_index in range(max_len):
        current_name = current[col_index] if col_index < len(current) else ""
        previous_name = previous[col_index] if col_index < len(previous) else ""
        original_name = table.headers[col_index].name if col_index < len(table.headers) else ""
        name = current_name or original_name or f"列{col_index + 1}"
        previous_non_empty = _non_empty_count(previous)
        if previous_non_empty > 1 and previous_name and current_name and previous_name != current_name and previous_non_empty <= _non_empty_count(current):
            name = f"{previous_name}-{current_name}"
        names.append(name)
    return names


def _infer_field_type(field_name: str) -> str:
    normalized = "".join(field_name.split()).lower()
    if any(token in normalized for token in ("日期", "时间", "date", "time")):
        return "date"
    if any(token in normalized for token in ("数", "量", "人口", "gdp", "收入", "金额", "预算", "病例", "检测", "比例", "率", "合计", "总计", "平均")):
        return "number"
    return "string"


def _anchor_with_header_row(location: LocationRef | None, header_row_index: int) -> LocationRef | None:
    if location is None:
        return None
    return LocationRef(
        doc_id=location.doc_id,
        page=location.page,
        sheet=location.sheet,
        paragraph_index=location.paragraph_index,
        table_index=location.table_index,
        row_index=header_row_index,
        col_index=location.col_index,
    )


class DefaultTemplateAnalyzer:
    """Infer target tables directly from parsed template tables."""

    def analyze(self, template_doc: CanonicalDocument) -> TemplateSpec:
        target_tables: list[TargetTableSpec] = []
        for index, table in enumerate(template_doc.tables):
            header_row_index = _select_header_row_index(table)
            header_names = _compose_header_names(table, header_row_index)
            schema = [
                FieldSpec(
                    field_id=f"{table.table_id}#field-{col_index}",
                    field_name=header_name,
                    normalized_name="".join(header_name.split()).strip().lower(),
                    data_type=_infer_field_type(header_name),
                    required=False,
                )
                for col_index, header_name in enumerate(header_names)
            ]
            description = " ".join(table.context_before).strip() or None
            target_tables.append(
                TargetTableSpec(
                    target_table_id=table.table_id,
                    logical_name=table.name or f"table_{index}",
                    schema=schema,
                    description=description,
                    local_constraints=_extract_local_constraints(table.table_id, description),
                    capacity=max(len(table.rows) - header_row_index - 1, 0),
                    supports_row_insert=True,
                    anchor=_anchor_with_header_row(table.location, header_row_index),
                )
            )
        return TemplateSpec(template_doc_id=template_doc.doc_id, target_tables=target_tables, write_mode="mixed")
