from celery import Celery

from docnexus.core.settings import get_settings

settings = get_settings()
celery_app = Celery("docnexus", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Shanghai",
    task_track_started=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_soft_time_limit=settings.task_timeout_seconds,
    task_time_limit=settings.task_timeout_seconds + 30,
    result_expires=86400,
    beat_schedule={
        "scan-automation-schedules": {
            "task": "docnexus.scan_schedules",
            "schedule": 30.0,
        },
        "recover-webhook-deliveries": {
            "task": "docnexus.recover_webhook_deliveries",
            "schedule": 60.0,
        },
    },
)
celery_app.autodiscover_tasks(["docnexus.worker"])
