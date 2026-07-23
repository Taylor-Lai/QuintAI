from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from celery.exceptions import SoftTimeLimitExceeded

from docnexus.ai.contracts import DocumentOperationInput, InformationExtractionInput, TableFillingInput
from docnexus.ai.workflows import handle_module_1_format, handle_module_2_extract, handle_module_3_fusion
from docnexus.db import SessionLocal, TaskRecord
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
                filename=str(payload["filename"]),
                file_type=Path(str(payload["filename"])).suffix.lstrip("."),
                fields_requested=fields,
                extracted_data=extract_result.extracted_data,
                content_preview=str(extract_result.extracted_data)[:1000],
            )
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
