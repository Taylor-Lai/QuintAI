from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from celery.exceptions import SoftTimeLimitExceeded

from docnexus.ai.contracts import DocumentOperationInput, InformationExtractionInput, TableFillingInput
from docnexus.ai.workflows import handle_module_1_format, handle_module_2_extract, handle_module_3_fusion
from docnexus.db import SessionLocal, TaskRecord, WorkflowDefinition, WorkflowRun
from docnexus.repositories.extractions import ExtractionRepository
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

    if kind == "document_edit":
        edit_result = handle_module_1_format(DocumentOperationInput(file_path=str(payload["file_path"]), natural_language_cmd=str(payload["command"])))
        if edit_result.status != "success":
            raise RuntimeError(edit_result.message)
        _update(task_id, output_path=edit_result.processed_file_path, output_name=payload["output_name"])
    elif kind == "document_extract":
        _update(task_id, progress=35, stage="正在提取字段")
        fields = [str(value) for value in payload["fields"]]
        extract_result = handle_module_2_extract(InformationExtractionInput(file_path=str(payload["file_path"]), target_entities=fields))
        if extract_result.status != "success":
            raise RuntimeError(extract_result.message)
        with SessionLocal() as db:
            ExtractionRepository.save_extraction(
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
        _update(task_id, result_data={"extracted_data": extract_result.extracted_data, "filename": payload["filename"]})
    elif kind == "table_fill":
        def progress_callback(_workflow_id: str, status: str, message: str) -> None:
            progress = 85 if status == "success" else 45
            _update(task_id, progress=progress, stage=message[:100])

        _update(task_id, progress=30, stage="正在分析模板和源文档")
        fill_result = handle_module_3_fusion(
            TableFillingInput(task_id=task_id, workspace_dir=str(payload["workspace_dir"]), user_request=payload.get("user_request") or None),
            progress_callback=progress_callback,
        )
        if fill_result.status != "success":
            raise RuntimeError(fill_result.error_msg)
        _update(task_id, output_path=fill_result.output_excel_path, output_name=payload["output_name"])
    else:
        raise ValueError(f"Unsupported task kind: {kind}")


@celery_app.task(bind=True, name="docnexus.process_task")
def process_task(self, task_id: str) -> None:
    try:
        _execute(task_id)
        if _is_cancelled(task_id):
            return
        _update(task_id, status="succeeded", progress=100, stage="处理完成", completed_at=datetime.now(), error_code=None, error_message=None)
    except SoftTimeLimitExceeded:
        _update(task_id, status="failed", stage="任务超时", error_code="TASK_TIMEOUT", error_message="任务超过最大执行时间", completed_at=datetime.now())
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
        _update(task_id, status="failed", stage="处理失败", error_code="TASK_FAILED", error_message=str(exc)[:2000], completed_at=datetime.now())
        raise
