"""Verify first, then reconcile via GET. Event names never establish financial settlement."""

import json
from fastapi import HTTPException
from sqlalchemy import select
from .db import Invoice, Persona, WebhookReceipt
from .paypal_client import PayPalError
from .paypal_provider import checkpoint, record_event


def handle_webhook(db, headers, raw, provider):
    webhook_id = provider.config.paypal_webhook_id.get_secret_value()
    if not webhook_id:
        raise HTTPException(
            503, "Sandbox webhook verification is not configured. Use authenticated invoice refresh."
        )
    if len(raw) > 512 * 1024:
        raise HTTPException(413, "Webhook exceeds the size limit.")
    try:
        event = json.loads(raw)
        event_id, event_type = event["id"], event["event_type"]
        if not isinstance(event_id, str) or not 1 <= len(event_id) <= 120 or not isinstance(event_type, str):
            raise ValueError
    except (ValueError, KeyError, TypeError):
        raise HTTPException(422, "Invalid webhook envelope.") from None
    fields = {
        "auth_algo": "paypal-auth-algo",
        "cert_url": "paypal-cert-url",
        "transmission_id": "paypal-transmission-id",
        "transmission_sig": "paypal-transmission-sig",
        "transmission_time": "paypal-transmission-time",
    }
    if any(not headers.get(name) for name in fields.values()):
        raise HTTPException(400, "Required PayPal signature headers are missing.")
    body = {key: headers[name] for key, name in fields.items()}
    body.update(webhook_id=webhook_id, webhook_event=event)
    try:
        verification = provider.client.request(
            "POST", "/v1/notifications/verify-webhook-signature", body=body
        )
    except PayPalError as error:
        raise HTTPException(502, str(error)) from None
    if verification.get("verification_status") != "SUCCESS":
        raise HTTPException(401, "Unverified PayPal webhook rejected.")
    receipt = db.scalar(select(WebhookReceipt).where(WebhookReceipt.event_id == event_id))
    if receipt and receipt.state in {"PROCESSED", "IGNORED"}:
        return {"received": True, "duplicate": True}
    if not receipt:
        receipt = WebhookReceipt(event_id=event_id, event_type=event_type)
        db.add(receipt)
    resource = event.get("resource", {})
    if not isinstance(resource, dict):
        raise HTTPException(422, "Invalid webhook resource.")
    nested_invoice = resource.get("invoice", {})
    if not isinstance(nested_invoice, dict):
        raise HTTPException(422, "Invalid webhook invoice resource.")
    remote_id = resource.get("id") or nested_invoice.get("id")
    invoice = (
        db.scalar(
            select(Invoice).where(Invoice.provider == "paypal_sandbox", Invoice.provider_id == remote_id)
        )
        if isinstance(remote_id, str)
        else None
    )
    if not invoice or not event_type.startswith("INVOICING.INVOICE."):
        receipt.state = "IGNORED"
        return {"received": True, "ignored": True}
    receipt.invoice_id = invoice.id
    checkpoint(db)
    try:
        provider.refresh(db, invoice)
    except HTTPException:
        receipt.state, receipt.error = "RETRYABLE", "AUTHORITATIVE_RECONCILIATION_FAILED"
        checkpoint(db)
        raise HTTPException(
            502, "Verified event could not be reconciled. No event-named payment state was applied."
        ) from None
    service_id = "paypal_webhook_service"
    if not db.get(Persona, service_id):
        db.add(
            Persona(
                id=service_id,
                role="service",
                name="PayPal Sandbox webhook service",
                email="no-email@example.test",
            )
        )
        db.flush()
    record_event(db, invoice, "VERIFIED_WEBHOOK_RECONCILED", "paypal_webhook_" + event_id, service_id)
    receipt.state, receipt.error = "PROCESSED", None
    return {"received": True, "status": invoice.status}
