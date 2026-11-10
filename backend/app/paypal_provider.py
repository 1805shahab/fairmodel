"""Actual Sandbox Invoicing v2. Durable local claims and authoritative reconciliation."""

import hashlib
import json
import re
from datetime import datetime, timezone
from decimal import Decimal
from urllib.parse import urlparse

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import select

from .config import settings
from .db import (
    Asset,
    Invoice,
    License,
    PaymentEvent,
    PaymentOperation,
    Report,
    Royalty,
    SandboxInvoiceDetail,
    now,
)
from .eligibility import approval_is_current
from .paypal_client import PayPalError, paypal_client, sandbox_link
from .paypal_models import Billing, Detail, DraftInvoice, Item, Money, Recipient, Snapshot, money_value


def checkpoint(db):
    # These journal writes must outlive a failed/rolled-back HTTP request.
    db.commit()
    db.connection().exec_driver_sql("BEGIN IMMEDIATE")
    db.expire_all()


def current_charge(db, royalty):
    if (
        not approval_is_current(db, royalty)
        or not Decimal(royalty.amount).is_finite()
        or Decimal(royalty.amount) <= 0
    ):
        raise HTTPException(409, "A positive, current, eligible artist-approved royalty is required.")
    if royalty.currency != "USD":
        raise HTTPException(422, "The initial Sandbox invoice adapter supports approved USD charges only.")


def record_event(db, invoice, kind, key, actor_id=None):
    existing = db.scalar(select(PaymentEvent).where(PaymentEvent.event_key == key))
    if not existing:
        db.add(
            PaymentEvent(
                invoice_id=invoice.id,
                event_key=key,
                kind=kind,
                actor_id=actor_id or invoice.artist_id,
                simulated=False,
            )
        )


class PayPalSandboxProvider:
    def __init__(self, client=paypal_client, config=settings):
        self.client, self.config = client, config

    def profile(self):
        try:
            merchant = Billing(
                email_address=self.config.paypal_sandbox_merchant_email.strip().lower()
            ).email_address
            buyer = Billing(
                email_address=self.config.paypal_sandbox_buyer_email.strip().lower()
            ).email_address
        except ValidationError:
            raise HTTPException(
                422,
                "Configure PAYPAL_SANDBOX_MERCHANT_EMAIL and PAYPAL_SANDBOX_BUYER_EMAIL with your test accounts.",
            ) from None
        if merchant == buyer or any(email.endswith((".test", ".invalid")) for email in (merchant, buyer)):
            raise HTTPException(
                422,
                "Use distinct merchant and buyer Sandbox accounts, not demo persona placeholder addresses.",
            )
        return merchant, buyer

    def payload(self, db, royalty):
        merchant, buyer = self.profile()
        license_ = db.get(License, royalty.license_id)
        asset = db.get(Asset, royalty.asset_id)
        wire = DraftInvoice(
            detail=Detail(
                invoice_number="FM-" + royalty.id[:22],
                reference="FairModel royalty " + royalty.id,
                currency_code=royalty.currency,
                invoice_date=datetime.now(timezone.utc).date().isoformat(),
            ),
            primary_recipients=[Recipient(billing_info=Billing(email_address=buyer))],
            items=[
                Item(
                    name="Additional licensed voice usage",
                    description=f"{license_.title}; campaign {asset.campaign.get('name', '')}; approved license version {asset.license_version}; royalty {royalty.id}. {royalty.calculation.get('explanation', '')}"[
                        :1000
                    ],
                    unit_amount=Money(currency_code=royalty.currency, value=royalty.amount),
                )
            ],
        )
        return {"invoice": wire.model_dump(mode="json"), "merchant_email": merchant, "buyer_email": buyer}

    def fail(self, db, operation, error):
        operation.state = (
            "UNKNOWN"
            if error.uncertain or error.category in {"INVALID_PROVIDER_RESPONSE", "DUPLICATE_INVOICE_NUMBER"}
            else "FAILED"
        )
        operation.error = error.category
        checkpoint(db)
        raise HTTPException(
            502 if operation.state == "FAILED" else 409,
            f"{error} {'The uncertain operation is held for reconciliation; no new write will be retried.' if operation.state == 'UNKNOWN' else 'Review provider access/settings before explicitly retrying.'}",
        ) from None

    def _bound(self, db, invoice):
        detail = db.scalar(select(SandboxInvoiceDetail).where(SandboxInvoiceDetail.invoice_id == invoice.id))
        if not detail or detail.merchant_key != self.client.merchant_key:
            raise HTTPException(
                409,
                "Invoice belongs to a different configured Sandbox merchant app or lacks provider evidence.",
            )
        return detail

    def snapshot(self, remote_id):
        if not re.fullmatch(r"INV2-[A-Z0-9-]{4,64}", remote_id or ""):
            raise PayPalError("INVALID_INVOICE_ID")
        try:
            snapshot = Snapshot.model_validate(
                self.client.request("GET", f"/v2/invoicing/invoices/{remote_id}")
            )
            if snapshot.id != remote_id:
                raise PayPalError("INVOICE_EVIDENCE_MISMATCH")
            return snapshot
        except ValidationError:
            raise PayPalError("INVALID_PROVIDER_RESPONSE") from None

    def validate_snapshot(self, snapshot, amount, currency, payload):
        try:
            number = snapshot.detail.get("invoice_number")
            recipient = snapshot.primary_recipients[0]["billing_info"]["email_address"].lower()
            issuer = snapshot.invoicer["email_address"].lower()
            if (
                number != payload["invoice"]["detail"]["invoice_number"]
                or snapshot.detail.get("reference") != payload["invoice"]["detail"]["reference"]
                or money_value(snapshot.amount.model_dump(), currency) != Decimal(amount)
                or issuer != payload["merchant_email"]
                or recipient != payload["buyer_email"]
                or len(snapshot.primary_recipients) != 1
            ):
                raise ValueError
            paid = (
                money_value(snapshot.payments["paid_amount"], currency)
                if snapshot.payments.get("paid_amount")
                else Decimal("0")
            )
            due = money_value(snapshot.due_amount.model_dump(), currency) if snapshot.due_amount else None
            refunded = (
                money_value(snapshot.refunds["refund_amount"], currency)
                if snapshot.refunds.get("refund_amount")
                else Decimal("0")
            )
            if paid > Decimal(amount) or refunded > paid or (due is not None and due > Decimal(amount)):
                raise ValueError
            return paid, due, refunded
        except (KeyError, IndexError, TypeError, ValueError, ValidationError):
            raise PayPalError("INVOICE_EVIDENCE_MISMATCH") from None

    def apply_snapshot(self, db, invoice, detail, snapshot, payload):
        paid, due, refunded = self.validate_snapshot(snapshot, invoice.amount, invoice.currency, payload)
        transactions = snapshot.payments.get("transactions", [])
        if not isinstance(transactions, list) or any(not isinstance(row, dict) for row in transactions):
            raise PayPalError("INVALID_PAYMENT_EVIDENCE")
        paypal_payments = [
            row for row in transactions if row.get("type") == "PAYPAL" and row.get("payment_id")
        ]
        try:
            paypal_paid = sum(
                (money_value(row.get("amount"), invoice.currency) for row in paypal_payments), Decimal("0")
            )
            if paypal_paid > paid or len({row["payment_id"] for row in paypal_payments}) != len(
                paypal_payments
            ):
                raise ValueError
        except (ValidationError, TypeError, ValueError):
            raise PayPalError("INVALID_PAYMENT_EVIDENCE") from None
        metadata = snapshot.detail.get("metadata", {})
        if not isinstance(metadata, dict):
            raise PayPalError("INVALID_PROVIDER_RESPONSE")
        stamp = metadata.get("last_update_time")
        if stamp and detail.provider_updated_at:
            try:
                if datetime.fromisoformat(stamp.replace("Z", "+00:00")) < datetime.fromisoformat(
                    detail.provider_updated_at.replace("Z", "+00:00")
                ):
                    raise PayPalError("STALE_PROVIDER_SNAPSHOT")
            except ValueError:
                raise PayPalError("INVALID_PROVIDER_TIMESTAMP") from None
        status = snapshot.status
        state = {
            "DRAFT": "DRAFT",
            "SENT": "SENT",
            "UNPAID": "SENT",
            "SCHEDULED": "SCHEDULED",
            "SHARED": "SENT",
            "VIEWED": "VIEWED",
            "PAYMENT_PENDING": "PAYMENT_PENDING",
            "CANCELLED": "CANCELLED",
            "AUTO_CANCELLED": "CANCELLED",
            "REFUNDED": "REFUNDED",
            "PARTIALLY_REFUNDED": "PARTIALLY_REFUNDED",
            "PARTIALLY_PAID": "PARTIALLY_PAID",
        }.get(status, "NEEDS_RECONCILIATION")
        if status == "PAID":
            # An event name alone never settles an invoice. Require current API totals and PayPal payment evidence.
            state = (
                "PAID"
                if paid == Decimal(invoice.amount)
                and paypal_paid == paid
                and due == 0
                and refunded == 0
                and len({row["payment_id"] for row in paypal_payments}) == len(paypal_payments)
                else "NEEDS_RECONCILIATION"
            )
        elif status in {"MARKED_AS_PAID", "PAID_EXTERNAL", "MARKED_AS_REFUNDED", "REFUNDED_EXTERNAL"}:
            state = "NEEDS_RECONCILIATION"
        elif refunded > 0:
            state = "REFUNDED" if refunded == paid else "PARTIALLY_REFUNDED"
        elif status != "PAYMENT_PENDING" and 0 < paid < Decimal(invoice.amount):
            state = "PARTIALLY_PAID"
        if invoice.status in {"PAID", "REFUNDED", "PARTIALLY_REFUNDED"} and state in {
            "DRAFT",
            "SENT",
            "SCHEDULED",
            "VIEWED",
            "PAYMENT_PENDING",
            "PARTIALLY_PAID",
        }:
            raise PayPalError("STALE_PROVIDER_SNAPSHOT")
        if Decimal(detail.paid_amount or "0") > paid and refunded == 0:
            raise PayPalError("STALE_PROVIDER_SNAPSHOT")
        if Decimal(detail.refunded_amount or "0") > refunded:
            raise PayPalError("STALE_PROVIDER_SNAPSHOT")
        detail.provider_status = status
        detail.paid_amount, detail.due_amount, detail.refunded_amount = (
            str(paid),
            str(due) if due is not None else None,
            str(refunded),
        )
        detail.last_synced_at, detail.provider_updated_at, detail.error = (
            now(),
            stamp or detail.provider_updated_at,
            None,
        )
        detail.payment_url = sandbox_link(metadata.get("recipient_view_url"))
        detail.due_date = snapshot.detail.get("payment_term", {}).get("due_date")
        detail.transactions = [
            {
                key: row[key]
                for key in ("type", "payment_id", "payment_date", "method", "amount")
                if key in row
            }
            for row in snapshot.payments.get("transactions", [])
        ]
        invoice.status = state
        event_hash = hashlib.sha256(
            json.dumps(
                {
                    "status": status,
                    "paid": str(paid),
                    "due": str(due),
                    "refund": str(refunded),
                    "updated": stamp,
                    "transactions": detail.transactions,
                },
                sort_keys=True,
            ).encode()
        ).hexdigest()
        record_event(db, invoice, "PAYPAL_SYNC_" + state, "paypal_sync_" + invoice.id + "_" + event_hash)

    def recover(self, operation):
        if operation.remote_id:
            return self.snapshot(operation.remote_id)
        result = self.client.request(
            "POST",
            "/v2/invoicing/search-invoices",
            body={
                "invoice_number": operation.payload["invoice"]["detail"]["invoice_number"],
                "reference": operation.payload["invoice"]["detail"]["reference"],
            },
            params={"page_size": 100},
        )
        matches = [
            item
            for item in result.get("items", [])
            if item.get("detail", {}).get("invoice_number")
            == operation.payload["invoice"]["detail"]["invoice_number"]
            and item.get("detail", {}).get("reference") == operation.payload["invoice"]["detail"]["reference"]
        ]
        if len(matches) != 1:
            raise PayPalError("UNCERTAIN_CREATE_REQUIRES_RECONCILIATION", uncertain=True)
        return self.snapshot(matches[0]["id"])

    def create_invoice(self, db, royalty):
        existing = db.scalar(select(Invoice).where(Invoice.royalty_id == royalty.id))
        if existing:
            if existing.provider != "paypal_sandbox":
                raise HTTPException(
                    409,
                    "This royalty already has a historical mock invoice. Use a separately eligible new case; history cannot be replaced.",
                )
            return existing
        if not self.config.paypal_allow_drafts:
            raise HTTPException(
                409,
                "Sandbox draft writes are disabled. Explicit owner authorization and PAYPAL_ALLOW_DRAFTS=true are required.",
            )
        current_charge(db, royalty)
        operation = db.scalar(
            select(PaymentOperation).where(
                PaymentOperation.royalty_id == royalty.id,
                PaymentOperation.kind == "create",
                PaymentOperation.provider == "paypal_sandbox",
            )
        )
        if operation and operation.merchant_key != self.client.merchant_key:
            raise HTTPException(
                409, "Do not switch merchant credentials while an invoice operation needs reconciliation."
            )
        if not operation:
            payload = self.payload(db, royalty)
            report = db.scalar(select(Report).where(Report.asset_id == royalty.asset_id))
            operation = PaymentOperation(
                royalty_id=royalty.id,
                kind="create",
                merchant_key=self.client.merchant_key,
                evidence_hash=report.result["input_hash"],
                payload=payload,
            )
            db.add(operation)
            checkpoint(db)
        try:
            if operation.state in {"INFLIGHT", "UNKNOWN", "SUCCEEDED"}:
                snapshot = self.recover(operation)
            else:
                current_charge(db, royalty)
                if operation.payload != self.payload(db, royalty):
                    raise HTTPException(
                        409,
                        "The frozen invoice inputs changed. Reconcile the prior operation before creating a new invoice.",
                    )
                operation.state = "INFLIGHT"
                checkpoint(db)
                current_charge(db, royalty)
                result = self.client.request(
                    "POST", "/v2/invoicing/invoices", body=operation.payload["invoice"]
                )
                remote_id = result.get("id")
                if not remote_id and result.get("href"):
                    link = urlparse(result["href"])
                    if (
                        link.scheme == "https"
                        and link.hostname == "api-m.sandbox.paypal.com"
                        and link.path.startswith("/v2/invoicing/invoices/")
                    ):
                        remote_id = link.path.rsplit("/", 1)[-1]
                if not remote_id:
                    raise PayPalError("INVALID_PROVIDER_RESPONSE", uncertain=True)
                operation.remote_id = remote_id
                checkpoint(db)
                snapshot = self.snapshot(remote_id)
            self.validate_snapshot(snapshot, royalty.amount, royalty.currency, operation.payload)
            # A checkpoint releases the SQLite lock. A concurrent reconciler can have
            # materialized this same accepted remote invoice while we reacquired it.
            existing = db.scalar(select(Invoice).where(Invoice.royalty_id == royalty.id))
            if existing:
                if existing.provider != "paypal_sandbox" or existing.provider_id != snapshot.id:
                    raise HTTPException(409, "Conflicting historical invoice requires reconciliation.")
                return existing
            invoice = Invoice(
                royalty_id=royalty.id,
                provider="paypal_sandbox",
                simulated=False,
                provider_id=snapshot.id,
                artist_id=royalty.artist_id,
                studio_id=royalty.studio_id,
                recipient=operation.payload["buyer_email"],
                amount=royalty.amount,
                currency=royalty.currency,
            )
            db.add(invoice)
            db.flush()
            detail = SandboxInvoiceDetail(
                invoice_id=invoice.id,
                merchant_key=operation.merchant_key,
                issuer=operation.payload["merchant_email"],
                invoice_number=operation.payload["invoice"]["detail"]["invoice_number"],
            )
            db.add(detail)
            record_event(db, invoice, "PAYPAL_DRAFT_CREATED", "paypal_created_" + invoice.id)
            self.apply_snapshot(db, invoice, detail, snapshot, operation.payload)
            operation.state, operation.remote_id, operation.error = "SUCCEEDED", snapshot.id, None
            return invoice
        except PayPalError as error:
            # A known remote ID or a failed read means a write may already have succeeded.
            if operation.remote_id or operation.state == "UNKNOWN":
                error.uncertain = True
            self.fail(db, operation, error)

    def refresh(self, db, invoice):
        detail = self._bound(db, invoice)
        operation = db.scalar(
            select(PaymentOperation).where(
                PaymentOperation.royalty_id == invoice.royalty_id, PaymentOperation.kind == "create"
            )
        )
        try:
            if not operation:
                raise PayPalError("MISSING_INVOICE_INTENT")
            self.apply_snapshot(db, invoice, detail, self.snapshot(invoice.provider_id), operation.payload)
        except PayPalError as error:
            detail.error = error.category
            checkpoint(db)
            raise HTTPException(502, str(error)) from None
        return invoice

    def send_invoice(self, db, invoice, actor, event_key):
        if actor.id != invoice.artist_id:
            raise HTTPException(403, "Only the assigned artist can send this Sandbox invoice.")
        if not self.config.paypal_allow_sending:
            raise HTTPException(
                409,
                "Sandbox sending is disabled. Explicit owner approval and PAYPAL_ALLOW_SENDING=true are required.",
            )
        royalty = db.get(Royalty, invoice.royalty_id)
        current_charge(db, royalty)
        self.refresh(db, invoice)
        operation = db.scalar(
            select(PaymentOperation).where(
                PaymentOperation.royalty_id == royalty.id, PaymentOperation.kind == "send"
            )
        )
        if invoice.status != "DRAFT":
            if operation:
                operation.state, operation.error = "SUCCEEDED", None
            return invoice
        if operation and operation.state in {"INFLIGHT", "UNKNOWN", "SUCCEEDED"}:
            raise HTTPException(
                409,
                "Previous send outcome is uncertain. Status was refreshed; no duplicate send was attempted.",
            )
        if not operation:
            operation = PaymentOperation(
                royalty_id=royalty.id,
                kind="send",
                merchant_key=self.client.merchant_key,
                evidence_hash="artist-approved-send",
                payload={"provider_id": invoice.provider_id},
                remote_id=invoice.provider_id,
            )
            db.add(operation)
        operation.state = "INFLIGHT"
        checkpoint(db)
        current_charge(db, royalty)
        try:
            self.client.request(
                "POST",
                f"/v2/invoicing/invoices/{invoice.provider_id}/send",
                body={"send_to_recipient": True, "send_to_invoicer": False},
            )
            operation.state = "SUCCEEDED"
            record_event(db, invoice, "PAYPAL_SEND_ACCEPTED", "paypal_sent_" + invoice.id, actor.id)
            checkpoint(db)
            return self.refresh(db, invoice)
        except PayPalError as error:
            self.fail(db, operation, error)

    def record_payment_event(self, *args, **kwargs):
        raise HTTPException(
            409,
            "Sandbox payment cannot be simulated. Pay manually on the actual PayPal-hosted invoice, then refresh.",
        )

    def get_invoice(self, db, invoice_id):
        invoice = db.get(Invoice, invoice_id)
        if not invoice:
            raise HTTPException(404, "Invoice not found.")
        return invoice

    def get_payment_status(self, db, invoice_id):
        return self.refresh(db, self.get_invoice(db, invoice_id)).status

    def list_invoices(self, db, actor):
        column = Invoice.artist_id if actor.role == "artist" else Invoice.studio_id
        return list(db.scalars(select(Invoice).where(column == actor.id).order_by(Invoice.created_at.desc())))
