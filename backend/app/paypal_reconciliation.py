"""Explicit, audited issuer typo repair for an already-existing Sandbox draft.

This path cannot create/send/update a PayPal invoice. Its transport exposes only
GET of the frozen remote ID; the original intent survives in an audit event.
"""

import copy
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select

from .db import Audit, Invoice, PaymentOperation, Persona, Report, Royalty, SandboxInvoiceDetail
from .paypal_provider import PayPalSandboxProvider, current_charge, record_event


class ExistingInvoiceReads:
    def __init__(self, client, remote_id):
        self.client, self.remote_id = client, remote_id

    @property
    def merchant_key(self):
        return self.client.merchant_key

    def request(self, method, path, **kwargs):
        if method != "GET" or path != f"/v2/invoicing/invoices/{self.remote_id}" or kwargs:
            raise HTTPException(409, "Issuer reconciliation permits only reading this existing invoice.")
        return self.client.request(method, path)


def reconcile_issuer(
    db,
    provider,
    *,
    operation_id,
    remote_id,
    amount,
    currency,
    recipient,
    merchant,
    actor_id,
    note,
    execute=False,
):
    if len(note.strip()) < 10:
        raise HTTPException(422, "An explanatory owner-authorized reconciliation note is required.")
    operation = db.get(PaymentOperation, operation_id)
    if (
        not operation
        or operation.provider != "paypal_sandbox"
        or operation.kind != "create"
        or operation.remote_id != remote_id
        or operation.state not in {"UNKNOWN", "SUCCEEDED"}
        or (operation.state == "UNKNOWN" and operation.error != "INVOICE_EVIDENCE_MISMATCH")
        or operation.merchant_key != provider.client.merchant_key
    ):
        raise HTTPException(409, "Existing draft operation or merchant binding does not match this repair.")
    royalty = db.get(Royalty, operation.royalty_id)
    actor = db.get(Persona, actor_id)
    if not royalty or not actor or actor.role != "artist" or actor.id != royalty.artist_id:
        raise HTTPException(403, "Only the assigned artist may authorize issuer reconciliation.")
    if royalty.currency != currency or Decimal(royalty.amount) != Decimal(amount):
        raise HTTPException(409, "Authorized amount/currency differs from the approved royalty.")
    current_charge(db, royalty)
    report = db.scalar(select(Report).where(Report.asset_id == royalty.asset_id))
    if not report or operation.evidence_hash != report.result.get("input_hash"):
        raise HTTPException(409, "The original invoice approval evidence changed; reconcile it separately.")
    configured_merchant, configured_buyer = provider.profile()
    if configured_merchant != merchant or configured_buyer != recipient:
        raise HTTPException(
            409, "Runtime merchant/buyer configuration differs from the authorized correction."
        )
    original = copy.deepcopy(operation.payload)
    if original.get("buyer_email") != recipient:
        raise HTTPException(409, "Frozen buyer cannot be changed by issuer reconciliation.")
    corrected = {**original, "merchant_email": merchant}
    read_provider = PayPalSandboxProvider(ExistingInvoiceReads(provider.client, remote_id), provider.config)
    snapshot = read_provider.snapshot(remote_id)
    # All original amount/reference/number/buyer/currency checks remain mandatory.
    paid, due, refunded = read_provider.validate_snapshot(
        snapshot, royalty.amount, royalty.currency, corrected
    )
    if snapshot.status != "DRAFT":
        raise HTTPException(409, "Only an existing, unsent PayPal draft supports this correction.")
    if paid != 0 or refunded != 0 or due != Decimal(royalty.amount):
        raise HTTPException(409, "Draft payment evidence is inconsistent; reconcile it separately.")
    existing = db.scalar(select(Invoice).where(Invoice.royalty_id == royalty.id))
    if existing:
        if (
            operation.state != "SUCCEEDED"
            or existing.provider != "paypal_sandbox"
            or existing.provider_id != remote_id
            or existing.amount != royalty.amount
            or existing.currency != royalty.currency
            or original != corrected
        ):
            raise HTTPException(409, "Conflicting existing invoice requires separate reconciliation.")
        return {"status": "ALREADY_RECONCILED", "invoice_id": existing.id, "remote_id": remote_id}
    if operation.state != "UNKNOWN" or original == corrected:
        raise HTTPException(409, "This operation does not have an unresolved issuer correction.")
    result = {
        "status": "READY",
        "remote_id": remote_id,
        "amount": royalty.amount,
        "currency": royalty.currency,
        "provider_status": snapshot.status,
        "merchant_matches_paypal": True,
        "provider_writes": 0,
    }
    if not execute:
        return result
    invoice = Invoice(
        royalty_id=royalty.id,
        provider="paypal_sandbox",
        simulated=False,
        provider_id=remote_id,
        artist_id=royalty.artist_id,
        studio_id=royalty.studio_id,
        recipient=recipient,
        amount=royalty.amount,
        currency=royalty.currency,
    )
    db.add(invoice)
    db.flush()
    detail = SandboxInvoiceDetail(
        invoice_id=invoice.id,
        merchant_key=operation.merchant_key,
        issuer=merchant,
        invoice_number=corrected["invoice"]["detail"]["invoice_number"],
    )
    db.add(detail)
    read_provider.apply_snapshot(db, invoice, detail, snapshot, corrected)
    # Preserve the complete original intent and the exact owner-approved delta.
    db.add(
        Audit(
            actor_id=actor_id,
            artist_id=royalty.artist_id,
            studio_id=royalty.studio_id,
            action="paypal.issuer_binding_corrected",
            entity_id=operation.id,
            detail={
                "original_payload": original,
                "corrected_merchant_email": merchant,
                "remote_invoice_id": remote_id,
                "note": note.strip(),
                "provider_writes": 0,
                "original_error": operation.error,
            },
        )
    )
    operation.payload = corrected
    operation.state, operation.error = "SUCCEEDED", None
    record_event(
        db, invoice, "PAYPAL_EXISTING_DRAFT_RECONCILED", "paypal_reconciled_" + operation.id, actor_id
    )
    db.flush()
    return {**result, "status": "RECONCILED", "invoice_id": invoice.id}
