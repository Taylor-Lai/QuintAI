"""Multi-source table filling adapter for the Any2table pipeline."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Callable

from docnexus.ai.llm import (
    LLM_PROVIDER,
    OPENAI_BASE_URL,
    OPENAI_MODEL,
    ZHIPU_BASE_URL,
    ZHIPU_MODEL,
)
from docnexus.ai.table_engine.app import build_orchestrator
from docnexus.ai.table_engine.cli import discover_assets
from docnexus.ai.table_engine.config import AppConfig

logger = logging.getLogger(__name__)


def _schema_classes():
    try:
        from docnexus.ai.contracts import Mod3_FusionOutput
    except ImportError:  # pragma: no cover - local package fallback
        from .contracts import Mod3_FusionOutput
    return Mod3_FusionOutput


def _write_fill_run_report(work_dir: Path, task_id: str, result) -> Path:
    """Persist a traceability report outside the temporary upload workspace."""
    report_dir = Path.cwd() / "reports" / "table_fill"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"{task_id}-fill-run-report.json"

    debug = dict(result.debug)
    checks = [check.to_dict() for check in result.verification_report.checks]
    warnings = list(result.fill_result.warnings)
    if result.verification_report.status != "pass":
        warnings.append(result.verification_report.summary)

    payload = {
        "schema_version": "1.0",
        "task_id": task_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "workspace_dir": str(work_dir),
        "input_summary": {
            "document_count": debug.get("document_count", 0),
            "source_document_count": debug.get("source_document_count", 0),
            "input_assets": debug.get("input_assets", []),
        },
        "target_tables": debug.get("target_tables", []),
        "template_fields": [
            field
            for table in debug.get("target_tables", [])
            for field in table.get("fields", [])
        ],
        "task_constraints": debug.get("task_constraints", []),
        "task_policy": debug.get("task_policy"),
        "task_plan": debug.get("task_plan"),
        "task_plan_execution": debug.get("task_plan_execution"),
        "output_path": result.fill_result.output_path,
        "verification_status": result.verification_report.status,
        "verification_summary": result.verification_report.summary,
        "checks": checks,
        "evidence_count": debug.get("evidence_count", 0),
        "candidate_stats": {
            "rule_candidate_count": debug.get("rule_candidate_count", 0),
            "agent_candidate_count": debug.get("agent_candidate_count", 0),
            "merged_candidate_count": debug.get("merged_candidate_count", 0),
            "rejected_candidate_count": debug.get("rejected_candidate_count", 0),
            "candidate_merge_warning_count": debug.get("candidate_merge_warning_count", 0),
        },
        "rag_result": debug.get("rag_result"),
        "route_plan": debug.get("route_plan", []),
        "selected_route": debug.get("selected_route"),
        "skill_runs": [
            {key: value for key, value in run.items() if key != "prompt_preview"}
            for run in debug.get("skill_runs", [])
        ],
        "llm_runs": [
            {key: value for key, value in run.items() if key not in {"response_preview", "error"}}
            for run in debug.get("llm_runs", [])
        ],
        "written_cell_count": len(result.fill_result.written_cells),
        "non_empty_written_cell_count": sum(
            1 for cell in result.fill_result.written_cells if cell.value not in (None, "", "未找到")
        ),
        "traceable_cell_count": sum(1 for cell in result.fill_result.written_cells if cell.evidence_ids),
        "debug": {
            key: debug.get(key)
            for key in (
                "runtime",
                "document_count",
                "source_document_count",
                "record_count",
                "evidence_count",
                "rule_candidate_count",
                "agent_candidate_count",
                "merged_candidate_count",
                "rejected_candidate_count",
                "candidate_merge_warning_count",
            )
            if key in debug
        },
        "warnings": warnings,
    }
    report_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return report_path


def handle_table_filling(
    input_data,
    progress_callback: Callable[[str, str, str], None] | None = None,
):
    Mod3_FusionOutput = _schema_classes()
    work_dir = Path(input_data.workspace_dir)
    user_request_content = input_data.user_request or "请根据源文档中的信息，自动填充模板表格。"
    (work_dir / "用户要求.txt").write_text(user_request_content, encoding="utf-8")

    try:
        if progress_callback:
            progress_callback(input_data.task_id, "processing", "Initializing multi-agent table filling pipeline.")

        llm_provider = LLM_PROVIDER
        llm_model = ZHIPU_MODEL if llm_provider == "zhipu" else OPENAI_MODEL
        llm_api_key_env = "ZHIPU_API_KEY" if llm_provider == "zhipu" else "OPENAI_API_KEY"
        llm_base_url = ZHIPU_BASE_URL if llm_provider == "zhipu" else OPENAI_BASE_URL

        config = AppConfig(
            enable_agent_runtime=True,
            agent_runtime_backend="langgraph",
            enable_llm_skill_execution=True,
            llm_provider=llm_provider,
            llm_model=llm_model,
            llm_api_key_env=llm_api_key_env,
            llm_base_url=llm_base_url or None,
            rag_backend="hybrid",
        )

        assets = discover_assets(work_dir)
        if progress_callback:
            progress_callback(input_data.task_id, "processing", f"Discovered {len(assets)} file assets.")

        orchestrator = build_orchestrator(config=config)
        if progress_callback:
            progress_callback(input_data.task_id, "processing", "Running multi-agent LangGraph orchestration.")

        result = orchestrator.run(assets)
        report_path = _write_fill_run_report(work_dir, input_data.task_id, result)
        if progress_callback:
            progress_callback(input_data.task_id, "success", "Table filling and verification completed.")

        warnings = list(result.fill_result.warnings)
        if result.verification_report.status == "fail":
            return Mod3_FusionOutput(
                status="failed",
                task_id=input_data.task_id,
                error_msg=result.verification_report.summary,
                warnings=[*warnings, f"fill_run_report={report_path}"],
            )
        if result.verification_report.status != "pass":
            warnings.append(result.verification_report.summary)
        warnings.append(f"fill_run_report={report_path}")

        return Mod3_FusionOutput(
            status="success",
            task_id=input_data.task_id,
            output_excel_path=str(result.fill_result.output_path),
            warnings=warnings,
        )

    except Exception:
        logger.exception("Table-filling pipeline failed for task %s", input_data.task_id)
        if progress_callback:
            progress_callback(input_data.task_id, "failed", "Table filling pipeline failed.")
        return Mod3_FusionOutput(
            status="failed",
            task_id=input_data.task_id,
            error_msg="表格填写流程执行失败，请查看服务端日志。",
        )
