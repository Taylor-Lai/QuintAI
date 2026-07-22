"""Task planners for table-filling requests.

The planner intentionally keeps deterministic parsing outside the LLM path so
API acceptance tests can verify complex user instructions repeatably.
"""

from __future__ import annotations

import re

from docnexus.ai.table_engine.core.models import CanonicalDocument, Constraint, TaskSpec, TemplateSpec

CN_DATE = r"(\d{4})\s*(?:\u5e74|-|/)\s*(\d{1,2})\s*(?:\u6708|-|/)\s*(\d{1,2})\s*(?:\u65e5)?"
DATE_RANGE_PATTERN = re.compile(
    rf"{CN_DATE}\s*(?:\u81f3|\u5230|-|~|--|through|to)\s*{CN_DATE}",
    re.IGNORECASE,
)
SINGLE_DATE_PATTERN = re.compile(CN_DATE, re.IGNORECASE)
ISO_DATETIME_PATTERN = re.compile(r"(\d{4}-\d{1,2}-\d{1,2}\s+\d{1,2}:\d{2}(?::\d{2})?(?:\.\d+)?)")
TOP_N_PATTERN = re.compile(
    r"(?:top|\u524d|\u53d6\u524d|\u6700\u9ad8|\u6700\u4f4e|\u6392\u540d\u524d|\u6392\u884c\u524d)\s*([0-9\u4e00\u4e8c\u4e09\u56db\u4e94\u516d\u4e03\u516b\u4e5d\u5341]+)",
    re.IGNORECASE,
)
COMPARISON_PATTERN = re.compile(
    r"([\u4e00-\u9fffA-Za-z0-9_/%.-]{1,30})\s*"
    r"(>=|<=|>|<|=|==|\u5927\u4e8e\u7b49\u4e8e|\u4e0d\u5c0f\u4e8e|"
    r"\u5c0f\u4e8e\u7b49\u4e8e|\u4e0d\u5927\u4e8e|\u5927\u4e8e|\u9ad8\u4e8e|"
    r"\u8d85\u8fc7|\u5c0f\u4e8e|\u4f4e\u4e8e|\u5c11\u4e8e|\u7b49\u4e8e|\u4e3a|is)\s*"
    r"(-?\d+(?:,\d{3})*(?:\.\d+)?)",
    re.IGNORECASE,
)

TASK_POLICY_PATTERNS = {
    "latest": [
        r"latest",
        r"\u6700\u540e\u4e00(?:\u5929|\u6761|\u884c)?",
        r"\u6700\u65b0",
        r"\u6700\u8fd1",
        r"\u622a\u81f3",
        r"\u53d6\u6700\u65b0",
        r"\u53d6\u6700\u540e",
    ],
    "earliest": [
        r"earliest",
        r"\u6700\u65e9",
        r"\u7b2c\u4e00(?:\u5929|\u6761|\u884c)?",
        r"\u53d6\u6700\u65e9",
        r"\u53d6\u7b2c\u4e00",
    ],
    "average": [r"average", r"avg", r"\u5e73\u5747", r"\u5747\u503c", r"\u5e73\u5747\u503c"],
    "all_dates": [
        r"all\s*dates",
        r"\u5168\u90e8\u65e5\u671f",
        r"\u6240\u6709\u65e5\u671f",
        r"\u6309\u65e5\u671f\u5c55\u5f00",
        r"\u9010\u65e5",
        r"\u6bcf\u5929",
        r"\u660e\u7ec6",
    ],
}

ENTITY_FIELD_HINTS = {
    "\u57ce\u5e02": ("\u57ce\u5e02", "\u57ce\u5e02\u540d", "city"),
    "\u56fd\u5bb6/\u5730\u533a": ("\u56fd\u5bb6/\u5730\u533a", "\u56fd\u5bb6", "\u5730\u533a", "country", "nation"),
    "\u7701\u4efd": ("\u7701\u4efd", "\u7701", "\u81ea\u6cbb\u533a", "\u76f4\u8f96\u5e02"),
    "\u7ad9\u70b9\u540d\u79f0": ("\u7ad9\u70b9\u540d\u79f0", "\u7ad9\u70b9", "\u76d1\u6d4b\u70b9"),
}
ENTITY_PREFIXES = (
    "\u8bf7",
    "\u5e2e\u6211",
    "\u7b5b\u9009",
    "\u53ea\u7b5b\u9009",
    "\u53ea\u4fdd\u7559",
    "\u4ec5\u4fdd\u7559",
    "\u53ea\u586b\u5199",
    "\u53ea\u586b",
    "\u586b\u5199",
    "\u63d0\u53d6",
    "\u7edf\u8ba1",
)
ENTITY_STOPWORDS = {
    "\u8bf7",
    "\u586b\u5199",
    "\u63d0\u53d6",
    "\u7edf\u8ba1",
    "\u7b5b\u9009",
    "\u5e76",
    "\u4e14",
    "\u7684",
    "\u6570\u636e",
    "\u8868\u683c",
    "\u6a21\u677f",
    "\u57ce\u5e02",
    "\u57ce\u5e02\u540d",
}


def _format_date(year: str, month: str, day: str) -> str:
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def _normalize_field_name(value: str) -> str:
    return "".join(str(value).split()).strip().lower().replace("_", "").replace("-", "")


def _target_fields(template_spec: TemplateSpec) -> list[str]:
    return [field.field_name for table in template_spec.target_tables for field in table.schema]


def _field_matches(source_field: str, target_field: str) -> bool:
    source = _normalize_field_name(source_field)
    target = _normalize_field_name(target_field)
    return bool(source and target and (source == target or source in target or target in source))


def _resolve_target_field(field_text: str, target_fields: list[str]) -> str | None:
    for target_field in target_fields:
        if _field_matches(field_text, target_field):
            return target_field
    return None


def _dedupe_constraints(constraints: list[Constraint]) -> list[Constraint]:
    deduped: list[Constraint] = []
    seen: set[tuple[str, str | None, str, str]] = set()
    for constraint in constraints:
        key = (constraint.kind, constraint.field, constraint.operator, str(constraint.value))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(constraint)
    return deduped


def _extract_date_constraints(user_request_doc: CanonicalDocument, request_text: str) -> list[Constraint]:
    date_range_match = DATE_RANGE_PATTERN.search(request_text)
    if date_range_match:
        y1, m1, d1, y2, m2, d2 = date_range_match.groups()
        return [
            Constraint(
                constraint_id=f"{user_request_doc.doc_id}#date-range",
                source="user_request",
                kind="date_range",
                field="\u65e5\u671f",
                operator="between",
                value={"start": _format_date(y1, m1, d1), "end": _format_date(y2, m2, d2)},
            )
        ]

    exact_datetime_match = ISO_DATETIME_PATTERN.search(request_text)
    if exact_datetime_match:
        return [
            Constraint(
                constraint_id=f"{user_request_doc.doc_id}#datetime",
                source="user_request",
                kind="exact_datetime",
                field="\u76d1\u6d4b\u65f6\u95f4",
                operator="equals",
                value=exact_datetime_match.group(1),
            )
        ]

    single_date_match = SINGLE_DATE_PATTERN.search(request_text)
    if single_date_match:
        return [
            Constraint(
                constraint_id=f"{user_request_doc.doc_id}#date",
                source="user_request",
                kind="exact_date",
                field="\u65e5\u671f",
                operator="equals",
                value=_format_date(*single_date_match.groups()),
            )
        ]
    return []


def _candidate_entity_values(request_text: str, hint: str) -> list[str]:
    values: list[str] = []
    quoted = re.findall(r"[\u201c\u201d\"'\u300a\u300b]([^'\"]{1,30})[\u201c\u201d\"'\u300a\u300b]", request_text)
    values.extend(value.strip() for value in quoted if value.strip())

    if hint == "\u57ce\u5e02":
        values.extend(re.findall(r"([\u4e00-\u9fff]{2,10}\u5e02)", request_text))
    elif hint == "\u56fd\u5bb6/\u5730\u533a":
        for value in ("China", "United States", "USA", "US", "\u4e2d\u56fd", "\u7f8e\u56fd", "\u65e5\u672c", "\u97e9\u56fd", "\u82f1\u56fd", "\u5fb7\u56fd", "\u6cd5\u56fd"):
            if value.lower() in request_text.lower():
                values.append(value)
    elif hint == "\u7701\u4efd":
        values.extend(re.findall(r"([\u4e00-\u9fff]{2,10}(?:\u7701|\u81ea\u6cbb\u533a|\u76f4\u8f96\u5e02))", request_text))
    elif hint == "\u7ad9\u70b9\u540d\u79f0":
        values.extend(re.findall(r"([\u4e00-\u9fffA-Za-z0-9_-]{2,20}(?:\u7ad9|\u76d1\u6d4b\u70b9))", request_text))

    cleaned: list[str] = []
    for value in values:
        value = value.strip(" ,，。；;、")
        changed = True
        while changed:
            changed = False
            for prefix in ENTITY_PREFIXES:
                if value.startswith(prefix) and len(value) > len(prefix):
                    value = value[len(prefix):]
                    changed = True
        if hint == "\u57ce\u5e02" and value in ENTITY_STOPWORDS:
            continue
        if hint == "\u57ce\u5e02" and not re.fullmatch(r"[\u4e00-\u9fff]{2,8}\u5e02", value):
            continue
        if value and value not in ENTITY_STOPWORDS and value not in cleaned:
            cleaned.append(value)
    return cleaned


def _extract_entity_constraints(user_request_doc: CanonicalDocument, request_text: str, target_fields: list[str]) -> list[Constraint]:
    constraints: list[Constraint] = []
    for canonical_field, aliases in ENTITY_FIELD_HINTS.items():
        target_field = next((field for field in target_fields if any(_field_matches(alias, field) for alias in aliases)), None)
        if target_field is None:
            continue
        for index, value in enumerate(_candidate_entity_values(request_text, canonical_field)):
            constraints.append(
                Constraint(
                    constraint_id=f"{user_request_doc.doc_id}#entity-{canonical_field}-{index}",
                    source="user_request",
                    kind="entity",
                    field=target_field,
                    operator="equals",
                    value=value,
                )
            )
    return constraints


def _comparison_operator(raw_operator: str) -> str:
    if raw_operator in {">=", "\u5927\u4e8e\u7b49\u4e8e", "\u4e0d\u5c0f\u4e8e", "不低于"}:
        return ">="
    if raw_operator in {"<=", "\u5c0f\u4e8e\u7b49\u4e8e", "\u4e0d\u5927\u4e8e"}:
        return "<="
    if raw_operator in {">", "\u5927\u4e8e", "\u9ad8\u4e8e", "\u8d85\u8fc7"}:
        return ">"
    if raw_operator in {"<", "\u5c0f\u4e8e", "\u4f4e\u4e8e", "\u5c11\u4e8e"}:
        return "<"
    return "=="


def _parse_positive_integer(value: str) -> int | None:
    if value.isdigit():
        return int(value)
    digits = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
    if value == "十":
        return 10
    if "十" in value:
        left, right = value.split("十", 1)
        tens = digits.get(left, 1) if left else 1
        ones = digits.get(right, 0) if right else 0
        return tens * 10 + ones
    return digits.get(value)


def _extract_comparison_constraints(user_request_doc: CanonicalDocument, request_text: str, target_fields: list[str]) -> list[Constraint]:
    constraints: list[Constraint] = []
    operator_pattern = (
        r"(>=|<=|>|<|=|==|大于等于|不小于|不低于|小于等于|不大于|大于|高于|超过|小于|低于|少于|等于|为|is)"
    )
    for target_field in sorted(target_fields, key=len, reverse=True):
        pattern = re.compile(
            rf"{re.escape(target_field)}\s*{operator_pattern}\s*(-?\d+(?:,\d{{3}})*(?:\.\d+)?)",
            re.IGNORECASE,
        )
        for match in pattern.finditer(request_text):
            raw_operator, raw_value = match.groups()
            value_text = raw_value.replace(",", "")
            value: int | float = float(value_text) if "." in value_text else int(value_text)
            constraints.append(
                Constraint(
                    constraint_id=f"{user_request_doc.doc_id}#filter-{len(constraints)}",
                    source="user_request",
                    kind="field_filter",
                    field=target_field,
                    operator=_comparison_operator(raw_operator),
                    value=value,
                )
            )
    return constraints


def _extract_sort_and_limit_constraints(user_request_doc: CanonicalDocument, request_text: str, target_fields: list[str]) -> list[Constraint]:
    constraints: list[Constraint] = []
    descending = bool(re.search(r"\u964d\u5e8f|\u4ece\u9ad8\u5230\u4f4e|\u7531\u9ad8\u5230\u4f4e|\u6700\u9ad8|top", request_text, re.IGNORECASE))
    ascending = bool(re.search(r"\u5347\u5e8f|\u4ece\u4f4e\u5230\u9ad8|\u7531\u4f4e\u5230\u9ad8|\u6700\u4f4e", request_text, re.IGNORECASE))

    sort_field = None
    sort_phrase = re.search(
        r"(?:\u6309|\u4f9d\u636e|by)\s*([\u4e00-\u9fffA-Za-z0-9_/%.-]{1,30})\s*(?:\u964d\u5e8f|\u5347\u5e8f|\u6392\u5e8f|desc|asc)",
        request_text,
        re.IGNORECASE,
    )
    if sort_phrase:
        sort_field = _resolve_target_field(sort_phrase.group(1), target_fields)
    if sort_field is None:
        scored_fields = [(request_text.rfind(field), field) for field in target_fields if field and field in request_text]
        if scored_fields:
            sort_field = max(scored_fields)[1]
    if (descending or ascending) and sort_field:
        constraints.append(
            Constraint(
                constraint_id=f"{user_request_doc.doc_id}#sort",
                source="user_request",
                kind="sort",
                field=sort_field,
                operator="desc" if descending and not ascending else "asc",
                value=sort_field,
            )
        )

    top_match = TOP_N_PATTERN.search(request_text)
    if top_match:
        limit = _parse_positive_integer(top_match.group(1))
        if limit is None:
            return constraints
        constraints.append(
            Constraint(
                constraint_id=f"{user_request_doc.doc_id}#limit",
                source="user_request",
                kind="limit",
                field=None,
                operator="top",
                value=limit,
            )
        )
    return constraints


def _extract_selected_field_constraints(user_request_doc: CanonicalDocument, request_text: str, target_fields: list[str]) -> list[Constraint]:
    selected = [field for field in target_fields if field and field in request_text]
    if len(selected) <= 1:
        return []
    return [
        Constraint(
            constraint_id=f"{user_request_doc.doc_id}#selected-fields",
            source="user_request",
            kind="selected_fields",
            field=None,
            operator="include",
            value=selected,
        )
    ]


def _extract_request_constraints(user_request_doc: CanonicalDocument, request_text: str, template_spec: TemplateSpec) -> list[Constraint]:
    constraints: list[Constraint] = []
    if request_text:
        constraints.append(
            Constraint(
                constraint_id=f"{user_request_doc.doc_id}#request",
                source="user_request",
                kind="request_text",
                field=None,
                operator="contains",
                value=request_text,
            )
        )
    fields = _target_fields(template_spec)
    constraints.extend(_extract_date_constraints(user_request_doc, request_text))
    constraints.extend(_extract_entity_constraints(user_request_doc, request_text, fields))
    constraints.extend(_extract_comparison_constraints(user_request_doc, request_text, fields))
    constraints.extend(_extract_sort_and_limit_constraints(user_request_doc, request_text, fields))
    constraints.extend(_extract_selected_field_constraints(user_request_doc, request_text, fields))
    return _dedupe_constraints(constraints)


def _infer_task_policy(request_text: str) -> str:
    lowered = request_text.lower()
    for policy in ("all_dates", "latest", "earliest", "average"):
        for pattern in TASK_POLICY_PATTERNS[policy]:
            if re.search(pattern, lowered, re.IGNORECASE):
                return policy
    return "all_dates"


class DefaultTaskPlanner:
    """Translate request text into a task spec with deterministic constraints."""

    def plan(
        self,
        user_request_doc: CanonicalDocument,
        template_spec: TemplateSpec,
        source_docs: list[CanonicalDocument],
    ) -> TaskSpec:
        request_text = "\n".join(block.text or "" for block in user_request_doc.blocks).strip()
        constraints = _extract_request_constraints(user_request_doc, request_text, template_spec)
        return TaskSpec(
            task_id=f"{user_request_doc.doc_id}#task",
            intent="fill_table",
            target_template_id=template_spec.template_doc_id,
            target_tables=[table.target_table_id for table in template_spec.target_tables],
            constraints=constraints,
            target_fields=_target_fields(template_spec),
            record_granularity="row",
            allow_inference=False,
            allow_empty_output=False,
            error_policy="strict",
            task_policy=_infer_task_policy(request_text),
        )


def _candidate_entity_values(request_text: str, hint: str) -> list[str]:
    values: list[str] = []
    quoted = re.findall(r"[\u201c\u201d\"'\u300a\u300b]([^'\"]{1,30})[\u201c\u201d\"'\u300a\u300b]", request_text)
    values.extend(value.strip() for value in quoted if value.strip())

    if hint == "\u57ce\u5e02":
        raw_values = re.findall(r"([\u4e00-\u9fff]{2,12}\u5e02)", request_text)
        for raw in raw_values:
            value = raw.strip()
            changed = True
            while changed:
                changed = False
                for prefix in (
                    "\u8bf7",
                    "\u7b5b\u9009",
                    "\u53ea\u7b5b\u9009",
                    "\u53ea\u4fdd\u7559",
                    "\u4ec5\u4fdd\u7559",
                    "\u4fdd\u7559",
                    "\u53ea\u586b\u5199",
                    "\u53ea\u586b",
                    "\u586b\u5199",
                ):
                    if value.startswith(prefix) and len(value) > len(prefix):
                        value = value[len(prefix):]
                        changed = True
            city_parts = re.findall(r"(?:^|[\u548c\u4e0e\u53ca\u3001,，\s])([\u4e00-\u9fff]{2,6}?\u5e02)", value)
            for city in city_parts or [value]:
                if any(token in city for token in ("\u586b", "\u586b\u5199", "\u5b57\u6bb5", "\u964d\u5e8f", "\u5347\u5e8f", "\u603b\u91cf")):
                    continue
                if city in ("\u57ce\u5e02", "\u57ce\u5e02\u540d"):
                    continue
                if re.fullmatch(r"[\u4e00-\u9fff]{2,6}\u5e02", city) and city not in values:
                    values.append(city)
    elif hint == "\u56fd\u5bb6/\u5730\u533a":
        for value in ("China", "United States", "USA", "US", "\u4e2d\u56fd", "\u7f8e\u56fd", "\u65e5\u672c", "\u97e9\u56fd", "\u82f1\u56fd", "\u5fb7\u56fd", "\u6cd5\u56fd"):
            if value.lower() in request_text.lower() and value not in values:
                values.append(value)
    elif hint == "\u7701\u4efd":
        values.extend(re.findall(r"([\u4e00-\u9fff]{2,10}(?:\u7701|\u81ea\u6cbb\u533a|\u76f4\u8f96\u5e02))", request_text))
    elif hint == "\u7ad9\u70b9\u540d\u79f0":
        values.extend(re.findall(r"([\u4e00-\u9fffA-Za-z0-9_-]{2,20}(?:\u7ad9|\u76d1\u6d4b\u70b9))", request_text))

    cleaned: list[str] = []
    for value in values:
        value = str(value).strip(" ,\u3001\uff0c\u3002\uff1b;")
        if value and value not in ENTITY_STOPWORDS and value not in cleaned:
            cleaned.append(value)
    return cleaned
