"""Lightweight multi-agent nodes for the first orchestration pass."""

from __future__ import annotations

import json
import re

from any2table.candidates.builders import (
    build_agent_candidates_from_skill_result,
    build_rule_candidates,
    candidates_to_structured_records,
    infer_target_entity_level,
    structured_record_to_candidate,
)
from any2table.core.models import Constraint, FieldSpec, VerificationCheck
from any2table.core.runtime import AgentState
from any2table.indexing.build_units import build_retrieval_units
from any2table.merging import merge_candidates
from any2table.skills.adapters import validate_structuring_skill_output
from any2table.skills.executor import execute_skill
from any2table.skills.renderer import render_skill_prompt

MAX_PARAGRAPH_COUNT = 150
MAX_PARAGRAPH_CHARS = 40000
MAX_TABLE_ROWS = 200


def _norm_field(value: object) -> str:
    return "".join(str(value or "").split()).strip().lower().replace("_", "").replace("-", "")


def _candidate_value(candidate, field_name: str):
    target = _norm_field(field_name)
    for key, value in candidate.values.items():
        key_norm = _norm_field(key)
        if key_norm == target or key_norm in target or target in key_norm:
            return value
    for key, value in candidate.row_identity.items():
        key_norm = _norm_field(key)
        if key_norm == target or key_norm in target or target in key_norm:
            return value
    return None


def _to_number(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        import re

        match = re.search(r"-?\d+(?:\.\d+)?", str(value))
        if match:
            try:
                return float(match.group(0))
            except ValueError:
                return None
    return None


def _entity_matches(candidate_value: object, expected_value: object) -> bool:
    if candidate_value in (None, "") or expected_value in (None, ""):
        return False
    candidate = str(candidate_value).strip()
    expected = str(expected_value).strip()
    if candidate == expected:
        return True
    candidate_loose = candidate.removesuffix("\u5e02")
    expected_loose = expected.removesuffix("\u5e02")
    return bool(candidate_loose and expected_loose and candidate_loose == expected_loose)


def _date_text(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return text[:10]


def _candidate_entity_group_key(candidate) -> tuple[str, str]:
    for field_name in ("\u56fd\u5bb6/\u5730\u533a", "\u56fd\u5bb6", "\u5730\u533a", "\u57ce\u5e02", "\u57ce\u5e02\u540d", "country", "city"):
        value = _candidate_value(candidate, field_name)
        if value not in (None, ""):
            return (_norm_field(field_name), str(value))
    return ("", "")


def _is_date_field_name(field_name: str | None) -> bool:
    normalized = _norm_field(field_name or "")
    return any(token in normalized for token in ("\u65e5\u671f", "\u65f6\u95f4", "date", "time"))


def _candidate_satisfies_task(candidate, task_spec) -> bool:
    entity_values_by_field: dict[str, list[object]] = {}
    date_ranges: list[tuple[str, str, str]] = []
    exact_dates: list[tuple[str, str]] = []
    field_filters: list[tuple[str, str, object]] = []

    for constraint in task_spec.constraints:
        if constraint.kind == "entity" and constraint.field:
            entity_values_by_field.setdefault(constraint.field, []).append(constraint.value)
        elif constraint.kind == "date_range" and constraint.field and isinstance(constraint.value, dict):
            start = str(constraint.value.get("start") or "")
            end = str(constraint.value.get("end") or "")
            if start and end:
                date_ranges.append((constraint.field, start, end))
        elif constraint.kind == "exact_date" and constraint.field:
            exact_dates.append((constraint.field, str(constraint.value)))
        elif constraint.kind == "field_filter" and constraint.field:
            field_filters.append((constraint.field, str(constraint.operator or ""), constraint.value))

    for field_name, expected_values in entity_values_by_field.items():
        candidate_value = _candidate_value(candidate, field_name)
        if expected_values and not any(_entity_matches(candidate_value, expected) for expected in expected_values):
            return False

    for field_name, start, end in date_ranges:
        value = _date_text(_candidate_value(candidate, field_name))
        if not value or value < start or value > end:
            return False

    for field_name, expected in exact_dates:
        value = _date_text(_candidate_value(candidate, field_name))
        if value != expected:
            return False

    for field_name, operator, threshold in field_filters:
        value = _to_number(_candidate_value(candidate, field_name))
        threshold_number = _to_number(threshold)
        if value is None or threshold_number is None:
            return False
        if operator in {">", "gt"} and not value > threshold_number:
            return False
        if operator in {">=", "gte"} and not value >= threshold_number:
            return False
        if operator in {"<", "lt"} and not value < threshold_number:
            return False
        if operator in {"<=", "lte"} and not value <= threshold_number:
            return False
        if operator in {"=", "==", "eq"} and not value == threshold_number:
            return False
    return True


def _finalize_candidates_by_task(candidates: list, task_spec):
    if not task_spec or not candidates:
        return candidates

    sort_field = None
    sort_reverse = False
    limit = None
    for constraint in task_spec.constraints:
        if constraint.kind == "sort" and constraint.field:
            sort_field = constraint.field
            sort_reverse = str(constraint.operator or "").lower() == "desc"
        elif constraint.kind == "limit":
            try:
                limit = max(int(constraint.value), 0)
            except (TypeError, ValueError):
                limit = None

    filtered_candidates = [candidate for candidate in candidates if _candidate_satisfies_task(candidate, task_spec)]
    if filtered_candidates:
        candidates = filtered_candidates

    if not sort_field and not limit:
        return candidates

    identity_fields = ["\u57ce\u5e02", "\u56fd\u5bb6/\u5730\u533a", "\u56fd\u5bb6", "\u5730\u533a", "\u7701\u4efd", "\u65e5\u671f", "date", "city"]
    deduped_by_key = {}
    ordered_keys = []
    for candidate in candidates:
        parts = [("__target_table_id__", candidate.target_table_id)]
        for field_name in identity_fields:
            value = _candidate_value(candidate, field_name)
            if value not in (None, ""):
                parts.append((_norm_field(field_name), str(value)))
        key = tuple(parts) if len(parts) > 1 else (("__candidate_id__", candidate.candidate_id),)
        previous = deduped_by_key.get(key)
        if previous is None:
            deduped_by_key[key] = candidate
            ordered_keys.append(key)
        elif candidate.confidence > previous.confidence:
            deduped_by_key[key] = candidate

    finalized = [deduped_by_key[key] for key in ordered_keys]
    if sort_field:
        def sort_key(candidate):
            value = _candidate_value(candidate, sort_field)
            group_key = _candidate_entity_group_key(candidate) if _is_date_field_name(sort_field) else ("", "")
            if _is_date_field_name(sort_field):
                return (*group_key, 0, _date_text(value))
            number = _to_number(value)
            if number is not None:
                return (*group_key, 0, number)
            return (*group_key, 1, "" if value is None else str(value))

        finalized.sort(key=sort_key, reverse=sort_reverse)
    if isinstance(limit, int) and limit > 0:
        finalized = finalized[:limit]
    return finalized


def _source_doc_summaries(state: AgentState) -> list[dict[str, object]]:
    summaries: list[dict[str, object]] = []
    for doc in state.source_docs:
        summaries.append(
            {
                "doc_id": doc.doc_id,
                "doc_type": doc.doc_type,
                "metadata": doc.metadata,
                "table_count": len(doc.tables),
                "block_count": len(doc.blocks),
            }
        )
    return summaries


def _source_docs_have_temporal_field(source_docs) -> bool:
    temporal_tokens = ("\u65e5\u671f", "\u65f6\u95f4", "date", "time")
    for doc in source_docs:
        for table in getattr(doc, "tables", []):
            for header in getattr(table, "headers", []):
                normalized = _norm_field(getattr(header, "name", ""))
                if any(token in normalized for token in temporal_tokens):
                    return True
        for block in getattr(doc, "blocks", []):
            text = getattr(block, "text", "") or ""
            if re.search(r"\d{4}[/-]\d{1,2}[/-]\d{1,2}|\d{4}\u5e74\d{1,2}\u6708\d{1,2}\u65e5", text):
                return True
    return False


def _ensure_temporal_schema_for_daily_sources(template_spec, task_spec, source_docs) -> None:
    if not _source_docs_have_temporal_field(source_docs):
        return
    request_text = "\n".join(
        str(constraint.value)
        for constraint in task_spec.constraints
        if constraint.kind == "request_text" and constraint.value
    )
    for target_table in template_spec.target_tables:
        field_names = [field.field_name for field in target_table.schema]
        if any(_is_date_field_name(field_name) for field_name in field_names):
            continue
        field_id = f"{target_table.target_table_id}#field-date"
        target_table.schema.append(
            FieldSpec(
                field_id=field_id,
                field_name="\u65e5\u671f",
                normalized_name="\u65e5\u671f",
                data_type="date",
                required=False,
            )
        )
        if "\u65e5\u671f" not in task_spec.target_fields:
            task_spec.target_fields.append("\u65e5\u671f")
    has_sort = any(constraint.kind == "sort" for constraint in task_spec.constraints)
    if not has_sort and re.search(r"(?:\u6309|\u4f9d\u636e)?\s*\u65e5\u671f\s*(?:\u5347\u5e8f|\u964d\u5e8f|\u6392\u5e8f)", request_text):
        descending = "\u964d\u5e8f" in request_text
        task_spec.constraints.append(
            Constraint(
                constraint_id=f"{task_spec.task_id}#auto-date-sort",
                source="schema_augmentation",
                kind="sort",
                field="\u65e5\u671f",
                operator="desc" if descending else "asc",
                value="\u65e5\u671f",
            )
        )


def _attach_skill(registry, state: AgentState, agent_name: str, skill_name: str, mode: str, inputs: dict[str, object]) -> None:
    if not registry.config.enable_skill_runtime or registry.skill_registry is None:
        return
    try:
        skill = registry.skill_registry.get(skill_name)
    except KeyError:
        state.add_log(agent_name, "skill_missing", {"skill": skill_name})
        return

    prompt = render_skill_prompt(skill, inputs)
    state.add_skill_run(
        agent=agent_name,
        skill=skill_name,
        mode=mode,
        input_keys=sorted(inputs.keys()),
        prompt_preview=prompt[:800],
    )
    state.add_log(agent_name, "skill_attached", {"skill": skill_name, "mode": mode})
    state.add_message(
        agent_name,
        "skill",
        f"{agent_name} attached skill {skill_name}.",
        {"skill": skill_name, "mode": mode},
    )


def _execute_skill_if_enabled(
    registry,
    state: AgentState,
    agent_name: str,
    skill_name: str,
    inputs: dict[str, object],
) -> dict[str, object] | None:
    if not registry.config.enable_llm_skill_execution:
        state.add_log(
            agent_name,
            "skill_execution_skipped",
            {"skill": skill_name, "reason": "llm_skill_execution_disabled"},
        )
        return None
    if registry.llm_client is None:
        state.add_log(
            agent_name,
            "skill_execution_skipped",
            {"skill": skill_name, "reason": "llm_client_unavailable"},
        )
        return None

    try:
        result, model = execute_skill(registry, skill_name=skill_name, inputs=inputs)
    except Exception as exc:  # pragma: no cover - network/provider dependent
        state.add_llm_run(
            agent=agent_name,
            skill=skill_name,
            status="error",
            error=str(exc),
        )
        state.add_log(
            agent_name,
            "skill_execution_failed",
            {"skill": skill_name, "error": str(exc)},
        )
        return None

    response_preview = json.dumps(result, ensure_ascii=False, default=str)[:800]
    state.add_llm_run(
        agent=agent_name,
        skill=skill_name,
        status="success",
        model=model,
        response_preview=response_preview,
    )
    state.add_skill_result(agent=agent_name, skill=skill_name, result=result, model=model)
    state.add_message(
        agent_name,
        "skill_result",
        f"{agent_name} executed skill {skill_name}.",
        {"skill": skill_name, "model": model, "result": result},
    )
    return result


def _run_skill(
    registry,
    state: AgentState,
    agent_name: str,
    skill_name: str,
    mode: str,
    inputs: dict[str, object],
) -> dict[str, object] | None:
    _attach_skill(registry, state, agent_name, skill_name, mode, inputs)
    if not registry.config.enable_skill_runtime or registry.skill_registry is None:
        return None
    return _execute_skill_if_enabled(registry, state, agent_name, skill_name, inputs)


def _skill_constraint_count(skill_result: dict[str, object]) -> int:
    constraints = skill_result.get("constraints", [])
    if isinstance(constraints, list):
        return len(constraints)
    if isinstance(constraints, dict):
        return len(constraints)
    return 0


def _paragraph_blocks_for_skill(source_doc) -> list[dict[str, object]]:
    blocks: list[dict[str, object]] = []
    total_chars = 0
    for block in source_doc.blocks:
        text = (block.text or "").strip()
        if not text:
            continue
        if len(blocks) >= MAX_PARAGRAPH_COUNT:
            break
        if blocks and total_chars + len(text) > MAX_PARAGRAPH_CHARS:
            break
        blocks.append(
            {
                "block_id": block.block_id,
                "text": text,
            }
        )
        total_chars += len(text)
    return blocks


def _table_blocks_for_skill(source_doc) -> list[dict[str, object]]:
    """将 xlsx/表格型文档的每一行转成文本块供 LLM Skill 处理。"""
    blocks: list[dict[str, object]] = []
    total_chars = 0
    for table in source_doc.tables:
        headers = [h.name for h in table.headers]
        for row in table.rows:
            if not headers:
                continue
            cells = [str(c.value) if c.value is not None else "" for c in row.cells]
            text = " | ".join(f"{h}: {v}" for h, v in zip(headers, cells) if v)
            if not text:
                continue
            if len(blocks) >= MAX_PARAGRAPH_COUNT:
                break
            if blocks and total_chars + len(text) > MAX_PARAGRAPH_CHARS:
                break
            blocks.append({"block_id": row.row_id, "text": text})
            total_chars += len(text)
        if len(blocks) >= MAX_PARAGRAPH_COUNT:
            break
    return blocks


def _build_table_skill_inputs(state: AgentState, source_doc) -> dict[str, object]:
    template_fields = []
    if state.template_spec is not None:
        for target_table in state.template_spec.target_tables:
            template_fields.extend(field.field_name for field in target_table.schema)

    tables_payload = []
    total_rows = 0
    for table in source_doc.tables:
        headers = [h.name for h in table.headers]
        if not headers:
            continue
        rows_payload = []
        for row in table.rows:
            if total_rows >= MAX_TABLE_ROWS:
                break
            rows_payload.append({h: c.value for h, c in zip(headers, row.cells)})
            total_rows += 1
        tables_payload.append({
            "table_id": table.table_id,
            "name": table.name or "",
            "headers": headers,
            "rows": rows_payload,
        })
        if total_rows >= MAX_TABLE_ROWS:
            break

    return {
        "user_request_doc": state.user_request_doc.to_dict() if state.user_request_doc else {},
        "task_spec": state.task_spec.to_dict() if state.task_spec else {},
        "template_fields": template_fields,
        "source_document": {
            "doc_id": source_doc.doc_id,
            "name": source_doc.file.name,
            "doc_type": source_doc.doc_type,
            "metadata": source_doc.metadata,
            "table_count": len(tables_payload),
            "truncated": total_rows >= MAX_TABLE_ROWS,
        },
        "tables": tables_payload,
    }


def _build_paragraph_skill_inputs(state: AgentState, source_doc) -> dict[str, object]:
    template_fields = []
    if state.template_spec is not None:
        for target_table in state.template_spec.target_tables:
            template_fields.extend(field.field_name for field in target_table.schema)
    if source_doc.blocks:
        paragraphs = _paragraph_blocks_for_skill(source_doc)
    else:
        paragraphs = _table_blocks_for_skill(source_doc)
    return {
        "user_request_doc": state.user_request_doc.to_dict() if state.user_request_doc else {},
        "task_spec": state.task_spec.to_dict() if state.task_spec else {},
        "template_fields": template_fields,
        "source_document": {
            "doc_id": source_doc.doc_id,
            "name": source_doc.file.name,
            "doc_type": source_doc.doc_type,
            "metadata": source_doc.metadata,
            "paragraph_count": len(paragraphs),
        },
        "paragraphs": paragraphs,
    }


def _legacy_rule_candidates(state: AgentState, records) -> list:
    target_fields = list(state.task_spec.target_fields) if state.task_spec else []
    entity_level = infer_target_entity_level(target_fields)
    return [
        structured_record_to_candidate(
            record,
            target_fields=target_fields,
            source_strategy="legacy_rule",
            entity_level=entity_level,
            metadata={"builder": "legacy_extractor"},
        )
        for record in records
    ]


class MasterAgent:
    """Central router that validates inputs and announces the execution plan."""

    def __init__(self, registry) -> None:
        self.registry = registry

    def run(self, state: AgentState) -> AgentState:
        if state.template_doc is None:
            raise ValueError("No template document found.")
        if state.user_request_doc is None:
            raise ValueError("No user request document found.")
        if not state.source_docs:
            raise ValueError("No source documents found.")

        skill_result = _run_skill(
            self.registry,
            state,
            agent_name="master",
            skill_name="any2table-task-understanding",
            mode="planning",
            inputs={
                "user_request_doc": state.user_request_doc.to_dict(),
                "template_spec": None,
                "source_doc_summaries": _source_doc_summaries(state),
            },
        )

        state.route_plan = ["table_agent", "router_agent", "retrieval_agent", "rag_agent", "coder_agent", "verifier_agent"]
        payload = {
            "document_count": len(state.documents),
            "source_document_count": len(state.source_docs),
            "route_plan": list(state.route_plan),
        }
        if skill_result:
            payload["llm_intent"] = skill_result.get("intent")
            payload["llm_constraint_count"] = _skill_constraint_count(skill_result)
            payload["llm_task_hints"] = skill_result.get("task_hints", [])
        state.add_message(
            "master",
            "routing",
            "Master agent prepared the multi-agent route.",
            payload,
        )
        return state


class TableAgent:
    """Reads the template schema and prepares the task specification."""

    def __init__(self, registry) -> None:
        self.registry = registry

    def run(self, state: AgentState) -> AgentState:
        template_spec = self.registry.template_analyzer.analyze(state.template_doc)
        planner = self.registry.get_task_planner("default")
        task_spec = planner.plan(
            user_request_doc=state.user_request_doc,
            template_spec=template_spec,
            source_docs=state.source_docs,
        )
        _ensure_temporal_schema_for_daily_sources(template_spec, task_spec, state.source_docs)

        state.template_spec = template_spec
        state.task_spec = task_spec
        state.selected_writer = (
            state.template_doc.doc_type
            if self.registry.config.writer_backend == "auto"
            else self.registry.config.writer_backend
        )
        state.add_message(
            "table_agent",
            "schema",
            "Table agent analyzed the target template and prepared fill instructions.",
            {
                "target_table_count": len(template_spec.target_tables),
                "target_field_count": len(task_spec.target_fields),
                "constraint_count": len(task_spec.constraints),
                "task_policy": task_spec.task_policy,
                "writer": state.selected_writer,
            },
        )
        return state


def _should_use_rag(state: AgentState) -> tuple[bool, str]:
    """Decide whether this task warrants RAG augmentation.

    RouterAgent runs before RetrievalAgent, so evidence_pack may not be available yet.
    Rules based on task_spec and source_docs (always available at routing time):

    - 3+ source documents: increased ambiguity benefits from RAG reranking.
    - 2+ constraints: selective task benefits from RAG filtering.
    - 5+ target fields: complex schema benefits from RAG field grounding.

    If evidence_pack is available (e.g. re-routing), also check field coverage.

    Returns (use_rag, reason_string).
    """
    task_spec = state.task_spec

    if task_spec is None:
        return False, "missing_task_spec"

    # Rule 1: multiple source docs increase ambiguity
    if len(state.source_docs) >= 3:
        return True, "multiple_source_docs_benefit_from_rag_reranking"

    # Rule 2: many constraints mean the task is selective
    if len(task_spec.constraints) >= 2:
        return True, "multiple_constraints_benefit_from_rag_filtering"

    # Rule 3: many target fields — complex schema benefits from semantic grounding
    if len(task_spec.target_fields) >= 5:
        return True, "complex_schema_benefits_from_rag_field_grounding"

    # Rule 4 (optional): if evidence is already available, check field coverage
    evidence_pack = state.evidence_pack
    if evidence_pack is not None:
        target_field_count = len(task_spec.target_fields)
        if target_field_count > 0:
            covered_fields: set[str] = set()
            for item in evidence_pack.items:
                if isinstance(item.content, dict):
                    covered_fields.update(item.content.keys())
            coverage = len(covered_fields & set(task_spec.target_fields)) / target_field_count
            if coverage < 0.5:
                return True, f"low_field_coverage_{coverage:.0%}_suggests_rag_needed"

    return False, "direct_route_sufficient"


class RouterAgent:
    """Decides whether the current task should stay on the direct path or go through RAG."""

    def __init__(self, registry) -> None:
        self.registry = registry

    def run(self, state: AgentState) -> AgentState:
        use_rag, reason = _should_use_rag(state)

        if use_rag and self.registry.config.rag_backend != "default":
            route = "rag"
            confidence = 0.8
        else:
            route = "direct"
            confidence = 1.0
            if use_rag:
                reason = f"rag_backend_is_default_noop; underlying_reason={reason}"

        state.selected_route = route
        state.router_decision = {
            "route": route,
            "reason": reason,
            "fallback_route": "direct",
            "confidence": confidence,
            "router_backend": self.registry.config.router_backend,
        }
        state.add_message(
            "router_agent",
            "route_decision",
            "Router agent selected the execution route.",
            dict(state.router_decision),
        )
        return state


class RetrievalAgent:
    """Collects candidate evidence with the configured retrieval backend."""

    def __init__(self, registry) -> None:
        self.registry = registry

    def run(self, state: AgentState) -> AgentState:
        backend = self.registry.config.retrieval_backend
        evidence_pack = self.registry.get_retriever(backend).retrieve(
            task_spec=state.task_spec,
            template_spec=state.template_spec,
            source_docs=state.source_docs,
        )
        state.evidence_pack = evidence_pack
        state.retrieval_units = build_retrieval_units(state.source_docs)

        skill_result = _run_skill(
            self.registry,
            state,
            agent_name="retrieval_agent",
            skill_name="any2table-candidate-selection",
            mode="selection",
            inputs={
                "task_spec": state.task_spec.to_dict() if state.task_spec else {},
                "template_spec": state.template_spec.to_dict() if state.template_spec else {},
                "evidence_candidates": {
                    "count": len(evidence_pack.items),
                    "sample_ids": [item.evidence_id for item in evidence_pack.items[:10]],
                },
            },
        )

        llm_selection_applied = False
        llm_selected_count = 0
        if skill_result:
            proposed_selected_ids = skill_result.get("selected_evidence_ids", [])
            llm_selected_count = len(proposed_selected_ids) if isinstance(proposed_selected_ids, list) else 0
            evidence_pack.retrieval_logs.append(
                {
                    "backend": "llm_skill",
                    "skill": "any2table-candidate-selection",
                    "selection_applied": False,
                    "proposed_selected_count": llm_selected_count,
                    "need_more_retrieval": bool(skill_result.get("need_more_retrieval")),
                }
            )
            state.add_log(
                "retrieval_agent",
                "llm_selection_suggested",
                {
                    "selection_applied": False,
                    "proposed_selected_count": llm_selected_count,
                    "reason": "selection_kept_advisory_until_candidate_merger_stage",
                },
            )

        state.add_message(
            "retrieval_agent",
            "retrieval",
            "Retrieval agent collected candidate evidence.",
            {
                "backend": backend,
                "route": state.selected_route,
                "evidence_count": len(evidence_pack.items),
                "coverage": evidence_pack.coverage,
                "llm_selection_applied": llm_selection_applied,
                "llm_selected_id_count": llm_selected_count,
            },
        )
        return state


class RAGAgent:
    """Optional augmentation layer that can later dispatch to table/doc/graph RAG backends."""

    def __init__(self, registry) -> None:
        self.registry = registry

    def run(self, state: AgentState) -> AgentState:
        if state.evidence_pack is None or state.task_spec is None or state.template_spec is None:
            raise ValueError("RAGAgent requires task spec, template spec, and evidence pack.")

        route = state.selected_route or "direct"
        rag_backend = self.registry.get_rag_backend(self.registry.config.rag_backend)
        result = rag_backend.run(
            route=route,
            task_spec=state.task_spec,
            template_spec=state.template_spec,
            source_docs=state.source_docs,
            evidence_pack=state.evidence_pack,
        )
        if result.evidence_pack is not None:
            state.evidence_pack = result.evidence_pack
        state.rag_result = result.to_dict()
        state.add_message(
            "rag_agent",
            "rag_route",
            "RAG agent evaluated the selected route.",
            dict(state.rag_result),
        )
        return state


class CoderAgent:
    """Turns evidence into structured records with rule extraction, candidate merging, and code execution."""

    def __init__(self, registry) -> None:
        self.registry = registry

    def run(self, state: AgentState) -> AgentState:
        extractor = self.registry.get_extractor(self.registry.config.extractor_backend)
        rule_candidates = build_rule_candidates(state.task_spec, state.template_spec, state.evidence_pack)
        legacy_records = []
        if not rule_candidates:
            legacy_records = extractor.extract(
                task_spec=state.task_spec,
                template_spec=state.template_spec,
                evidence_pack=state.evidence_pack,
            )
            rule_candidates = _legacy_rule_candidates(state, legacy_records)

        agent_candidates = []
        for source_doc in state.source_docs:
            if not source_doc.blocks and not source_doc.tables:
                continue

            if source_doc.blocks:
                skill_name = "any2table-paragraph-structuring"
                skill_inputs = _build_paragraph_skill_inputs(state, source_doc)
                content_key = "paragraphs"
                mode = "paragraph_extraction"
            else:
                skill_name = "any2table-table-row-extraction"
                skill_inputs = _build_table_skill_inputs(state, source_doc)
                content_key = "tables"
                mode = "table_extraction"

            if not skill_inputs.get(content_key):
                continue

            skill_result = _run_skill(
                self.registry,
                state,
                agent_name="coder_agent",
                skill_name=skill_name,
                mode=mode,
                inputs=skill_inputs,
            )
            if not skill_result:
                continue

            valid, error_msg = validate_structuring_skill_output(skill_result)
            if not valid:
                state.add_log("coder_agent", "skill_output_invalid", {
                    "source_doc_id": source_doc.doc_id,
                    "skill": skill_name,
                    "error": error_msg,
                })
                continue

            doc_candidates = build_agent_candidates_from_skill_result(
                task_spec=state.task_spec,
                template_spec=state.template_spec,
                source_doc=source_doc,
                skill_result=skill_result,
            )
            agent_candidates.extend(doc_candidates)
            state.add_log(
                "coder_agent",
                f"{mode}_completed",
                {
                    "source_doc_id": source_doc.doc_id,
                    "skill": skill_name,
                    "content_count": len(skill_inputs[content_key]),
                    "candidate_count": len(doc_candidates),
                },
            )

        target_entity_level = infer_target_entity_level(list(state.task_spec.target_fields) if state.task_spec else [])
        merge_result = merge_candidates(
            rule_candidates=rule_candidates,
            agent_candidates=agent_candidates,
            target_entity_level=target_entity_level,
        )
        merged_candidates = merge_result.merged_candidates
        if not merged_candidates and legacy_records:
            merged_candidates = _legacy_rule_candidates(state, legacy_records)
        finalized_candidates = _finalize_candidates_by_task(merged_candidates, state.task_spec)
        if len(finalized_candidates) != len(merged_candidates) or finalized_candidates != merged_candidates:
            state.add_log(
                "coder_agent",
                "candidate_finalized_by_task_constraints",
                {
                    "before_count": len(merged_candidates),
                    "after_count": len(finalized_candidates),
                },
            )
            merged_candidates = finalized_candidates

        records = candidates_to_structured_records(merged_candidates)
        records = self.registry.get_compute_engine("python").compute(records=records, task_spec=state.task_spec)

        state.rule_candidates = rule_candidates
        state.agent_candidates = agent_candidates
        state.merged_candidates = merged_candidates
        state.rejected_candidates = merge_result.rejected_candidates
        state.candidate_merge_warnings = merge_result.warnings
        state.records = records

        if merge_result.warnings:
            state.add_log(
                "coder_agent",
                "candidate_merge_warnings",
                {"warnings": merge_result.warnings[:20], "warning_count": len(merge_result.warnings)},
            )

        state.add_message(
            "coder_agent",
            "record_build",
            "Coder agent converted evidence into structured records.",
            {
                "selected_route": state.selected_route,
                "rule_candidate_count": len(rule_candidates),
                "agent_candidate_count": len(agent_candidates),
                "merged_candidate_count": len(merged_candidates),
                "rejected_candidate_count": len(merge_result.rejected_candidates),
                "merge_warning_count": len(merge_result.warnings),
                "record_count": len(records),
            },
        )
        return state


class VerifierAgent:
    """Writes the final output and performs lightweight verification."""

    def __init__(self, registry) -> None:
        self.registry = registry

    def run(self, state: AgentState) -> AgentState:
        writer = self.registry.get_writer(state.selected_writer or state.template_doc.doc_type)
        fill_result = writer.write(
            template_doc=state.template_doc,
            template_spec=state.template_spec,
            records=state.records,
        )
        verification_report = self.registry.get_verifier(self.registry.config.verifier_backend).verify(
            task_spec=state.task_spec,
            template_spec=state.template_spec,
            evidence_pack=state.evidence_pack,
            records=state.records,
            fill_result=fill_result,
        )
        state.fill_result = fill_result
        state.verification_report = verification_report

        skill_result = _run_skill(
            self.registry,
            state,
            agent_name="verifier_agent",
            skill_name="any2table-verification",
            mode="verification",
            inputs={
                "task_spec": state.task_spec.to_dict() if state.task_spec else {},
                "template_spec": state.template_spec.to_dict() if state.template_spec else {},
                "selected_records": {
                    "count": len(state.records),
                    "sample_record_ids": [record.record_id for record in state.records[:10]],
                },
                "fill_result": {
                    "output_path": fill_result.output_path,
                    "written_cell_count": len(fill_result.written_cells),
                },
            },
        )

        if skill_result:
            raw_status = str(skill_result.get("status", "warning")).lower()
            normalized_status = raw_status if raw_status in {"pass", "warning", "fail"} else "warning"
            issues = skill_result.get("issues", [])
            issue_count = len(issues) if isinstance(issues, list) else 0
            summary = str(skill_result.get("reasoning_summary", "")).strip()
            message = summary or f"LLM verification reported {issue_count} issue(s)."
            verification_report.checks.append(
                VerificationCheck(
                    name="llm_skill_review",
                    status=normalized_status,
                    message=message,
                )
            )
            if normalized_status in {"warning", "fail"} and verification_report.status == "pass":
                verification_report.status = normalized_status
            if summary:
                verification_report.summary = f"{verification_report.summary} LLM review: {summary}"

        state.add_message(
            "verifier_agent",
            "verification",
            "Verifier agent completed output generation and validation.",
            {
                "output_path": fill_result.output_path,
                "verification_status": verification_report.status,
                "llm_review_applied": bool(skill_result),
            },
        )
        return state
