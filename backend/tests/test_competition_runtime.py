"""Runtime tests for the competition operations added in generation v2."""

from __future__ import annotations

from datetime import datetime

import pytest
from cryptography.fernet import Fernet
from docnexus.db import (
    AutomationSchedule,
    Base,
    DocumentRecord,
    Organization,
    OrganizationMember,
    Subscription,
    TaskRecord,
    User,
    WebhookDelivery,
    WebhookEndpoint,
    WorkflowDefinition,
    WorkflowRun,
)
from docnexus.services import task_progress, webhooks
from docnexus.services.quality import extraction_quality, safely_repair_fields, table_quality
from docnexus.services.scheduling import cron_matches, next_cron_time
from docnexus.worker import tasks as worker_tasks
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def _factory(tmp_path, name: str):
    engine = create_engine(f"sqlite:///{tmp_path / name}")
    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine)


def _identity(db, suffix: str = "1") -> tuple[User, Organization]:
    user = User(
        id=f"user-{suffix}",
        username=f"runner-{suffix}",
        email=f"runner-{suffix}@example.com",
        password_hash="x",
    )
    organization = Organization(
        id=f"org-{suffix}",
        owner_id=user.id,
        name=f"测试组织 {suffix}",
        slug=f"test-org-{suffix}",
    )
    membership = OrganizationMember(
        id=f"membership-{suffix}",
        organization_id=organization.id,
        user_id=user.id,
        role="owner",
    )
    subscription = Subscription(
        id=f"subscription-{suffix}",
        organization_id=organization.id,
        plan="starter",
        limits={"members": 3, "documents": 500, "monthly_runs": 200, "storage_bytes": 2 * 1024**3},
        usage={"monthly_runs": 0},
    )
    user.active_organization_id = organization.id
    db.add_all([user, organization, membership, subscription])
    db.commit()
    return user, organization


def test_webhook_publish_and_delivery_lifecycle(tmp_path, monkeypatch) -> None:
    engine, factory = _factory(tmp_path, "webhooks.db")
    key = Fernet.generate_key()
    cipher = Fernet(key)
    monkeypatch.setattr(webhooks, "SessionLocal", factory)
    monkeypatch.setattr(webhooks, "_cipher", lambda: cipher)
    queued: list[str] = []
    monkeypatch.setattr(webhooks.celery_app, "send_task", lambda _name, args: queued.append(args[0]))

    with factory() as db:
        _, organization = _identity(db)
        matching = WebhookEndpoint(
            id="endpoint-match",
            organization_id=organization.id,
            name="任务回调",
            url="https://example.com/hook",
            secret_hash="hash",
            secret_ciphertext=cipher.encrypt(b"signing-secret").decode(),
            events=["task.succeeded"],
        )
        ignored = WebhookEndpoint(
            id="endpoint-ignore",
            organization_id=organization.id,
            name="其他事件",
            url="https://example.com/ignored",
            secret_hash="hash",
            secret_ciphertext=cipher.encrypt(b"ignored").decode(),
            events=["task.failed"],
        )
        db.add_all([matching, ignored])
        db.commit()

    assert webhooks.publish_event(None, "task.succeeded", {}) == []
    delivery_ids = webhooks.publish_event("org-1", "task.succeeded", {"task_id": "task-1"})
    assert delivery_ids == queued
    assert len(delivery_ids) == 1

    captured: dict[str, object] = {}

    class Response:
        status_code = 204

        @staticmethod
        def raise_for_status() -> None:
            return None

    def fake_post(url, *, content, headers, timeout):
        captured.update(url=url, content=content, headers=headers, timeout=timeout)
        return Response()

    monkeypatch.setattr(webhooks.httpx, "post", fake_post)
    webhooks.deliver_webhook.run(delivery_ids[0])

    with factory() as db:
        delivery = db.get(WebhookDelivery, delivery_ids[0])
        assert delivery.status == "delivered"
        assert delivery.response_status == 204
        assert delivery.attempts == 1
        assert delivery.delivered_at is not None
    assert captured["url"] == "https://example.com/hook"
    assert captured["timeout"] == 5
    assert str(captured["headers"]["X-HuiwenRongtong-Signature"]).startswith("sha256=")
    assert webhooks.decrypt_secret(cipher.encrypt(b"plain").decode()) == "plain"
    with pytest.raises(ValueError, match="签名密钥"):
        webhooks.decrypt_secret(None)

    engine.dispose()


def test_webhook_cancels_delivery_for_inactive_endpoint(tmp_path, monkeypatch) -> None:
    engine, factory = _factory(tmp_path, "cancelled-webhook.db")
    monkeypatch.setattr(webhooks, "SessionLocal", factory)
    with factory() as db:
        _, organization = _identity(db, "2")
        endpoint = WebhookEndpoint(
            id="endpoint-off",
            organization_id=organization.id,
            name="停用端点",
            url="https://example.com/off",
            secret_hash="hash",
            events=["*"],
            active=False,
        )
        delivery = WebhookDelivery(
            id="delivery-off",
            organization_id=organization.id,
            endpoint_id=endpoint.id,
            event="task.failed",
            payload={},
        )
        db.add_all([endpoint, delivery])
        db.commit()

    webhooks.deliver_webhook.run("missing")
    webhooks.deliver_webhook.run("delivery-off")
    with factory() as db:
        assert db.get(WebhookDelivery, "delivery-off").status == "cancelled"
    engine.dispose()


def test_task_progress_reset_and_missing_task_paths(tmp_path, monkeypatch) -> None:
    engine, factory = _factory(tmp_path, "progress.db")
    monkeypatch.setattr(task_progress, "SessionLocal", factory)
    with factory() as db:
        user, _ = _identity(db, "3")
        task = TaskRecord(
            id="task-progress",
            celery_task_id="celery-progress",
            user_id=user.id,
            kind="table_fill",
            payload={},
            status="running",
            progress=50,
            completed_steps=6,
            total_steps=12,
        )
        db.add(task)
        db.commit()

    task_progress.report_step("missing", "none", "不存在", "running", 0, 1)
    task_progress.reset_progress("missing")
    task_progress.report_step("task-progress", "load", "加载", "running", 1, 12)
    task_progress.reset_progress("task-progress")
    with factory() as db:
        task = db.get(TaskRecord, "task-progress")
        assert (task.progress, task.completed_steps, task.total_steps) == (0, 0, 12)
    assert task_progress.serialize_events("task-progress") == []
    engine.dispose()


def test_worker_state_updates_and_schedule_status(tmp_path, monkeypatch) -> None:
    engine, factory = _factory(tmp_path, "worker-update.db")
    monkeypatch.setattr(worker_tasks, "SessionLocal", factory)
    with factory() as db:
        user, organization = _identity(db, "4")
        document = DocumentRecord(
            id="document-4",
            user_id=user.id,
            organization_id=organization.id,
            filename="input.txt",
            file_type="txt",
            storage_path="input.txt",
        )
        workflow = WorkflowDefinition(
            id="workflow-4",
            user_id=user.id,
            organization_id=organization.id,
            name="字段提取",
            status="active",
            nodes=[],
        )
        schedule = AutomationSchedule(
            id="schedule-4",
            organization_id=organization.id,
            workflow_id=workflow.id,
            document_id=document.id,
            user_id=user.id,
            name="每日运行",
            cron_expression="0 9 * * *",
        )
        task = TaskRecord(
            id="task-4",
            celery_task_id="celery-4",
            user_id=user.id,
            organization_id=organization.id,
            kind="document_extract",
            payload={"schedule_id": schedule.id},
            status="queued",
        )
        run = WorkflowRun(
            id="run-4",
            user_id=user.id,
            organization_id=organization.id,
            workflow_id=workflow.id,
            document_id=document.id,
            task_id=task.id,
        )
        db.add_all([document, workflow, schedule, task, run])
        db.commit()

    worker_tasks._update("missing", status="running")
    worker_tasks._update("task-4", status="running", progress=35, stage="解析输入")
    assert worker_tasks._is_cancelled("task-4") is False
    worker_tasks._update("task-4", status="succeeded", progress=100, stage="完成")
    worker_tasks._update("task-4", status="succeeded", progress=100)
    with factory() as db:
        run = db.get(WorkflowRun, "run-4")
        workflow = db.get(WorkflowDefinition, "workflow-4")
        schedule = db.get(AutomationSchedule, "schedule-4")
        assert (run.status, run.progress, run.current_node) == ("succeeded", 100, "完成")
        assert workflow.runs_count == 1
        assert schedule.last_status == "succeeded"
        task = db.get(TaskRecord, "task-4")
        task.cancel_requested = True
        db.commit()
    assert worker_tasks._is_cancelled("task-4") is True
    assert worker_tasks._is_cancelled("missing") is True
    worker_tasks._update("task-4", status="failed", error_message="boom")
    engine.dispose()


def test_schedule_scanner_handles_invalid_and_valid_schedules(tmp_path, monkeypatch) -> None:
    engine, factory = _factory(tmp_path, "schedules.db")
    monkeypatch.setattr(worker_tasks, "SessionLocal", factory)
    queued: list[tuple[list[str], str]] = []
    monkeypatch.setattr(
        worker_tasks.process_task,
        "apply_async",
        lambda *, args, task_id: queued.append((args, task_id)),
    )
    now = datetime(2000, 1, 1)
    with factory() as db:
        user, organization = _identity(db, "5")
        document = DocumentRecord(
            id="document-5",
            user_id=user.id,
            organization_id=organization.id,
            filename="source.txt",
            file_type="txt",
            storage_path="source.txt",
        )
        valid_workflow = WorkflowDefinition(
            id="workflow-valid",
            user_id=user.id,
            organization_id=organization.id,
            name="有效流程",
            status="active",
            nodes=[{"type": "extract", "fields": ["负责人", "金额"]}],
            rules=[{"field": "金额", "type": "required"}],
        )
        invalid_workflow = WorkflowDefinition(
            id="workflow-invalid",
            user_id=user.id,
            organization_id=organization.id,
            name="无效流程",
            status="draft",
            nodes=[],
        )
        valid = AutomationSchedule(
            id="schedule-valid",
            organization_id=organization.id,
            workflow_id=valid_workflow.id,
            document_id=document.id,
            user_id=user.id,
            name="有效计划",
            cron_expression="0 9 * * *",
            next_run_at=now,
        )
        invalid = AutomationSchedule(
            id="schedule-invalid",
            organization_id=organization.id,
            workflow_id=invalid_workflow.id,
            user_id=user.id,
            name="无效计划",
            cron_expression="0 9 * * *",
            next_run_at=now,
        )
        db.add_all([document, valid_workflow, invalid_workflow, valid, invalid])
        db.commit()

    assert worker_tasks.scan_schedules.run() == {"queued": 1}
    assert len(queued) == 1
    with factory() as db:
        valid = db.get(AutomationSchedule, "schedule-valid")
        invalid = db.get(AutomationSchedule, "schedule-invalid")
        task = db.query(TaskRecord).one()
        assert valid.last_status == "queued"
        assert valid.next_run_at > now
        assert invalid.status == "paused"
        assert invalid.last_status == "invalid"
        assert task.payload["fields"] == ["负责人", "金额"]
        assert task.payload["schedule_id"] == valid.id
    engine.dispose()


def test_quality_and_scheduler_edge_cases() -> None:
    assert extraction_quality([], []) == {
        "kind": "extraction",
        "field_count": 0,
        "completeness": 0,
        "evidence_coverage": 0,
        "average_confidence": 0,
        "errors": 0,
        "warnings": 0,
        "requires_review": False,
    }
    repaired, changes = safely_repair_fields([{"name": "数量", "value": 3}, {"name": "备注", "value": "正常"}])
    assert repaired == [{"name": "数量", "value": 3}, {"name": "备注", "value": "正常"}]
    assert changes == []
    quality = table_quality(
        {
            "written_cell_count": 4,
            "non_empty_written_cell_count": 3,
            "traceable_cell_count": 2,
            "verification_status": "fail",
            "checks": [{"status": "fail"}, "ignored"],
            "warnings": ["缺少一项"],
        }
    )
    assert quality["completeness"] == 0.75
    assert quality["checks_failed"] == 1
    assert quality["requires_review"] is True
    with pytest.raises(ValueError, match="五个字段"):
        cron_matches("0 9 * *", datetime.now())
    with pytest.raises(ValueError, match="步长"):
        cron_matches("*/0 9 * * *", datetime.now())
    with pytest.raises(ValueError, match="超出"):
        cron_matches("61 9 * * *", datetime.now())
    with pytest.raises(ValueError, match="时区"):
        next_cron_time("0 9 * * *", "Mars/Olympus")
