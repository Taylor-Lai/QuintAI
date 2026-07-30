"""Signed webhook event creation and delivery helpers."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import uuid
from datetime import datetime, timedelta

import httpx
from cryptography.fernet import Fernet

from docnexus.core.settings import get_settings
from docnexus.db import SessionLocal, WebhookDelivery, WebhookEndpoint
from docnexus.worker.celery_app import celery_app


def _cipher() -> Fernet:
    secret_key = get_settings().require_secret_key()
    key = base64.urlsafe_b64encode(hashlib.sha256(secret_key.encode()).digest())
    return Fernet(key)


def decrypt_secret(ciphertext: str | None) -> str:
    if not ciphertext:
        raise ValueError("Webhook 缺少可用的签名密钥")
    return _cipher().decrypt(ciphertext.encode()).decode()


def _enqueue_delivery(delivery_id: str) -> bool:
    try:
        celery_app.send_task("docnexus.deliver_webhook", args=[delivery_id])
        return True
    except Exception as exc:
        with SessionLocal() as db:
            delivery = db.get(WebhookDelivery, delivery_id)
            if delivery is not None:
                delivery.status = "queue_failed"
                delivery.error_message = str(exc)[:1000]
                db.commit()
        return False


def publish_event(organization_id: str | None, event: str, payload: dict) -> list[str]:
    if not organization_id:
        return []
    delivery_ids: list[str] = []
    with SessionLocal() as db:
        endpoints = (
            db.query(WebhookEndpoint)
            .filter_by(organization_id=organization_id, active=True)
            .all()
        )
        for endpoint in endpoints:
            if event not in (endpoint.events or []) and "*" not in (endpoint.events or []):
                continue
            delivery = WebhookDelivery(
                id=uuid.uuid4().hex,
                organization_id=organization_id,
                endpoint_id=endpoint.id,
                event=event,
                payload={"event": event, "created_at": datetime.now().isoformat(), "data": payload},
            )
            db.add(delivery)
            delivery_ids.append(delivery.id)
        db.commit()
    for delivery_id in delivery_ids:
        _enqueue_delivery(delivery_id)
    return delivery_ids


def recover_webhook_deliveries(limit: int = 100) -> int:
    """Requeue broker failures, exhausted transient failures, and stale queued records."""
    cutoff = datetime.now() - timedelta(minutes=2)
    with SessionLocal() as db:
        rows = (
            db.query(WebhookDelivery)
            .filter(
                WebhookDelivery.attempts < 3,
                (
                    WebhookDelivery.status.in_(["queue_failed", "failed"])
                    | ((WebhookDelivery.status == "queued") & (WebhookDelivery.updated_at < cutoff))
                ),
            )
            .order_by(WebhookDelivery.updated_at.asc())
            .limit(limit)
            .all()
        )
        delivery_ids = [row.id for row in rows]
        for row in rows:
            row.status = "queued"
            row.error_message = None
            row.updated_at = datetime.now()
        db.commit()
    return sum(1 for delivery_id in delivery_ids if _enqueue_delivery(delivery_id))


@celery_app.task(bind=True, name="docnexus.deliver_webhook", max_retries=2)
def deliver_webhook(self, delivery_id: str) -> None:
    with SessionLocal() as db:
        delivery = db.get(WebhookDelivery, delivery_id)
        if delivery is None:
            return
        endpoint = db.get(WebhookEndpoint, delivery.endpoint_id)
        if endpoint is None or not endpoint.active:
            delivery.status = "cancelled"
            db.commit()
            return
        body = json.dumps(delivery.payload, ensure_ascii=False, separators=(",", ":")).encode()
        secret = decrypt_secret(endpoint.secret_ciphertext)
        signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        delivery.attempts += 1
        delivery.status = "delivering"
        db.commit()
        try:
            response = httpx.post(
                endpoint.url,
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "X-HuiwenRongtong-Event": delivery.event,
                    "X-HuiwenRongtong-Delivery": delivery.id,
                    "X-HuiwenRongtong-Signature": f"sha256={signature}",
                },
                timeout=5,
            )
            delivery.response_status = response.status_code
            response.raise_for_status()
            delivery.status = "delivered"
            delivery.delivered_at = datetime.now()
            delivery.error_message = None
            db.commit()
        except Exception as exc:
            delivery.status = "failed"
            delivery.error_message = str(exc)[:1000]
            db.commit()
            if self.request.retries < self.max_retries:
                raise self.retry(exc=exc, countdown=2 ** self.request.retries * 3)
