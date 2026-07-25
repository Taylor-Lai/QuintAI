from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

from celery.exceptions import SoftTimeLimitExceeded

from docnexus.ai.contracts import DocumentOperationInput, InformationExtractionInput, TableFillingInput
from docnexus.ai.workflows import handle_module_1_format, handle_module_2_extract, handle_module_3_fusion
from docnexus.db import (
    AutomationSchedule,
    DocumentRecord,
    ReviewRecord,
    SessionLocal,
    TaskRecord,
    WorkflowDefinition,
    WorkflowRun,
)
from docnexus.repositories.extractions import ExtractionRepository
from docnexus.repositories.tasks import TaskRepository
from docnexus.services.quality import extraction_quality, table_quality
from docnexus.services.scheduling import next_cron_time
from docnexus.services.task_progress import report_step
from docnexus.services.webhooks import publish_event
from docnexus.worker.celery_app import celery_app

logger = logging.getLogger(__name__)


def _update(task_id: str, **values) -> None:
    with SessionLocal() as db:
        record = db.get(TaskRecord, task_id)
        if record is None:
            return
        for key, value in values.items():
            setattr(record, key, value)
        workflow_run = db.query(WorkflowRun).filter(WorkflowRun.task_id == task_id).first()
        if workflow_run is not None:
            if "progress" in values:
                workflow_run.progress = int(values["progress"])
            if "stage" in values:
                workflow_run.current_node = str(values["stage"])
            if values.get("status") == "succeeded":
                was_succeeded = workflow_run.status == "succeeded"
                workflow_run.status = "succeeded"
                workflow_run.completed_at = values.get("completed_at") or datetime.now()
                if not was_succeeded:
                    workflow = db.get(WorkflowDefinition, workflow_run.workflow_id)
                    if workflow is not None:
                        workflow.runs_count += 1
            elif values.get("status") == "failed":
                workflow_run.status = "failed"
                workflow_run.error_message = str(values.get("error_message") or "任务执行失败")
                workflow_run.completed_at = values.get("completed_at") or datetime.now()
            elif values.get("status") in {"running", "retrying"}:
                workflow_run.status = str(values["status"])
                workflow_run.started_at = workflow_run.started_at or datetime.now()
        schedule_id = (record.payload or {}).get("schedule_id")
        if schedule_id and values.get("status") in {"succeeded", "failed"}:
            schedule = db.get(AutomationSchedule, str(schedule_id))
            if schedule is not None:
                schedule.last_status = str(values["status"])
        db.commit()


def _is_cancelled(task_id: str) -> bool:
    with SessionLocal() as db:
        record = db.get(TaskRecord, task_id)
        return record is None or record.cancel_requested or record.status == "cancelled"


def _execute(task_id: str) -> None:
    with SessionLocal() as db:
        record = db.get(TaskRecord, task_id)
        if record is None or record.cancel_requested:
            return
        payload = dict(record.payload)
        kind = record.kind
        total_steps = record.total_steps
        record.status = "running"
        record.progress = 10
        record.stage = "正在解析文件"
        record.started_at = datetime.now()
        record.attempts += 1
        workflow_run = db.query(WorkflowRun).filter(WorkflowRun.task_id == task_id).first()
        if workflow_run is not None:
            workflow_run.status = "running"
            workflow_run.started_at = datetime.now()
            workflow_run.progress = 10
            workflow_run.current_node = "正在解析文件"
        db.commit()

    report_step(task_id, "prepare", "任务进程已接收，正在加载输入", "running", 0, total_steps)

    if kind == "document_edit":
        report_step(task_id, "prepare", "文档和编辑指令已加载", "completed", 1, 4)
        report_step(task_id, "document_edit", "正在理解并执行文档编辑指令", "running", 1, 4)
        edit_result = handle_module_1_format(DocumentOperationInput(file_path=str(payload["file_path"]), natural_language_cmd=str(payload["command"])))
        if edit_result.status != "success":
            raise RuntimeError(edit_result.message)
        report_step(task_id, "document_edit", "文档编辑指令执行完成", "completed", 2, 4)
        report_step(task_id, "persist", "正在保存编辑后的文档", "running", 2, 4)
        _update(task_id, output_path=edit_result.processed_file_path, output_name=payload["output_name"])
        report_step(task_id, "persist", "编辑后的文档已保存", "completed", 3, 4)
    elif kind == "document_extract":
        fields = [str(value) for value in payload["fields"]]
        report_step(task_id, "prepare", f"文档已加载，共需提取 {len(fields)} 个字段", "completed", 1, 5)
        report_step(task_id, "extract", "正在解析文档并提取目标字段", "running", 1, 5)
        extract_result = handle_module_2_extract(InformationExtractionInput(file_path=str(payload["file_path"]), target_entities=fields))
        if extract_result.status != "success":
            raise RuntimeError(extract_result.message)
        report_step(task_id, "extract", "目标字段提取完成", "completed", 2, 5)
        report_step(task_id, "evidence", "正在生成证据链与置信度", "running", 2, 5)
        with SessionLocal() as db:
            extraction = ExtractionRepository.save_extraction(
                db=db,
                user_id=str(payload["user_id"]),
                task_id=task_id,
                document_id=payload.get("document_id"),
                filename=str(payload["filename"]),
                file_type=Path(str(payload["filename"])).suffix.lstrip("."),
                fields_requested=fields,
                extracted_data=extract_result.extracted_data,
                content_preview=str(extract_result.extracted_data)[:1000],
                validation_rules=payload.get("validation_rules") or [],
            )
            if payload.get("document_id"):
                from docnexus.db import DocumentRecord
                document = db.get(DocumentRecord, str(payload["document_id"]))
                if document:
                    document.status = "needs_review"
                    document.content_preview = str(extract_result.extracted_data)[:2000]
                    db.commit()
            review = db.query(ReviewRecord).filter(ReviewRecord.extraction_id == extraction.id).first()
            review_fields = list(review.fields or []) if review else []
            issues = list(review.validation_results or []) if review else []
        report_step(task_id, "evidence", "证据链与置信度已生成", "completed", 3, 5)
        report_step(task_id, "quality", "正在执行完整性和业务规则校验", "running", 3, 5)
        quality = extraction_quality(review_fields, issues)
        evidence = {
            "field_count": len(review_fields),
            "items": [
                {
                    "field": item.get("name"),
                    "snippet": item.get("evidence", ""),
                    "source_page": item.get("source_page"),
                    "confidence": item.get("confidence", 0),
                }
                for item in review_fields
            ],
        }
        _update(
            task_id,
            result_data={"extracted_data": extract_result.extracted_data, "filename": payload["filename"]},
            quality_report=quality,
            evidence_summary=evidence,
        )
        report_step(task_id, "quality", "质量检查完成，结果已进入人工复核", "completed", 4, 5, quality)
    elif kind == "table_fill":
        def progress_callback(
            node_code: str,
            status: str,
            message: str,
            completed_steps: int,
            total_steps: int,
        ) -> None:
            report_step(task_id, node_code, message, status, completed_steps, total_steps)

        fill_result = handle_module_3_fusion(
            TableFillingInput(task_id=task_id, workspace_dir=str(payload["workspace_dir"]), user_request=payload.get("user_request") or None),
            progress_callback=progress_callback,
        )
        if fill_result.status != "success":
            raise RuntimeError(fill_result.error_msg)
        quality = table_quality(fill_result.report_data)
        evidence = {
            "items": list(fill_result.report_data.get("evidence_items") or [])[:100],
            "cell_traces": list(fill_result.report_data.get("cell_traces") or [])[:200],
        }
        _update(
            task_id,
            output_path=fill_result.output_excel_path,
            output_name=payload["output_name"],
            result_data={"report_path": fill_result.report_path, "warnings": fill_result.warnings},
            quality_report=quality,
            evidence_summary=evidence,
        )
    else:
        raise ValueError(f"Unsupported task kind: {kind}")


@celery_app.task(bind=True, name="docnexus.process_task")
def process_task(self, task_id: str) -> None:
    try:
        _execute(task_id)
        if _is_cancelled(task_id):
            return
        with SessionLocal() as db:
            record = db.get(TaskRecord, task_id)
            total_steps = record.total_steps if record else 1
        report_step(task_id, "delivery", "结果文件和质量报告已就绪", "completed", total_steps, total_steps)
        _update(task_id, status="succeeded", progress=100, stage="处理完成", completed_at=datetime.now(), error_code=None, error_message=None)
        with SessionLocal() as db:
            record = db.get(TaskRecord, task_id)
            organization_id = record.organization_id if record else None
        publish_event(organization_id, "task.succeeded", {"task_id": task_id})
    except SoftTimeLimitExceeded:
        _update(task_id, status="failed", stage="任务超时", error_code="TASK_TIMEOUT", error_message="任务超过最大执行时间", completed_at=datetime.now())
        with SessionLocal() as db:
            record = db.get(TaskRecord, task_id)
            organization_id = record.organization_id if record else None
        publish_event(organization_id, "task.failed", {"task_id": task_id, "error_code": "TASK_TIMEOUT"})
        raise
    except Exception as exc:
        logger.exception("Task %s failed", task_id)
        with SessionLocal() as db:
            record = db.get(TaskRecord, task_id)
            if record is None or record.cancel_requested:
                return
            if self.request.retries < record.max_attempts - 1:
                record.status = "retrying"
                record.stage = "执行失败，等待自动重试"
                record.error_message = str(exc)[:2000]
                db.commit()
                raise self.retry(exc=exc, countdown=min(30, 2 ** self.request.retries * 5))
            completed_steps = record.completed_steps
            total_steps = record.total_steps
            organization_id = record.organization_id
        report_step(
            task_id,
            "failure",
            "任务执行失败",
            "failed",
            completed_steps,
            total_steps,
            {"error": str(exc)[:500]},
        )
        _update(task_id, status="failed", stage="处理失败", error_code="TASK_FAILED", error_message=str(exc)[:2000], completed_at=datetime.now())
        publish_event(organization_id, "task.failed", {"task_id": task_id, "error_code": "TASK_FAILED"})
        raise


@celery_app.task(name="docnexus.scan_schedules")
def scan_schedules() -> dict[str, int]:
    """Enqueue due schedules; Celery Beat invokes this lightweight scan."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    queued = 0
    with SessionLocal() as db:
        schedules = (
            db.query(AutomationSchedule)
            .filter(
                AutomationSchedule.status == "active",
                AutomationSchedule.next_run_at.is_not(None),
                AutomationSchedule.next_run_at <= now,
            )
            .all()
        )
        for schedule in schedules:
            workflow = db.get(WorkflowDefinition, schedule.workflow_id)
            document = db.get(DocumentRecord, schedule.document_id) if schedule.document_id else None
            extraction_node = next((node for node in (workflow.nodes if workflow else []) if node.get("type") == "extract"), None)
            fields = [str(item).strip() for item in (extraction_node or {}).get("fields", []) if str(item).strip()]
            if workflow is None or workflow.status != "active" or document is None or not fields:
                schedule.last_status = "invalid"
                schedule.status = "paused"
                continue
            task = TaskRepository.create(db, schedule.user_id, "document_extract", {})
            task.organization_id = schedule.organization_id
            task.max_attempts = schedule.retry_limit + 1
            run = WorkflowRun(
                id=uuid.uuid4().hex,
                user_id=schedule.user_id,
                organization_id=schedule.organization_id,
                workflow_id=workflow.id,
                document_id=document.id,
                task_id=task.id,
            )
            task.payload = {
                "file_path": document.storage_path,
                "filename": document.filename,
                "fields": fields,
                "user_id": schedule.user_id,
                "document_id": document.id,
                "validation_rules": workflow.rules or [],
                "workflow_run_id": run.id,
                "schedule_id": schedule.id,
            }
            document.status = "processing"
            schedule.last_run_at = now
            schedule.last_status = "queued"
            schedule.next_run_at = next_cron_time(
                schedule.cron_expression,
                schedule.timezone,
                after=now.replace(tzinfo=timezone.utc),
            )
            db.add(run)
            db.commit()
            process_task.apply_async(args=[task.id], task_id=task.celery_task_id)
            queued += 1
        db.commit()
    return {"queued": queued}
