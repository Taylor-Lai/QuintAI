"""Signed webhook event creation and delivery helpers."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import uuid
from datetime import datetime

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
        try:
            celery_app.send_task("docnexus.deliver_webhook", args=[delivery_id])
        except Exception:
            # The queued record remains visible and can be retried after Redis recovers.
            pass
    return delivery_ids


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
                    "X-QuintAI-Event": delivery.event,
                    "X-QuintAI-Delivery": delivery.id,
                    "X-QuintAI-Signature": f"sha256={signature}",
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
