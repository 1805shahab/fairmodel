from abc import ABC, abstractmethod
from decimal import Decimal, InvalidOperation

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import Invoice, PaymentEvent, Persona, Royalty, SandboxInvoiceDetail, uid

PAYMENT_NOTICE = "DEMO / SIMULATED PAYMENT — NO REAL FUNDS TRANSFERRED"


class PaymentProvider(ABC):
    @abstractmethod
    def create_invoice(self, session: Session, royalty: Royalty) -> Invoice: ...

    @abstractmethod
    def send_invoice(self, session: Session, invoice: Invoice, actor: Persona, event_key: str) -> Invoice: ...

    @abstractmethod
    def get_invoice(self, session: Session, invoice_id: str) -> Invoice: ...

    @abstractmethod
    def list_invoices(self, session: Session, actor: Persona) -> list[Invoice]: ...

    @abstractmethod
    def get_payment_status(self, session: Session, invoice_id: str) -> str: ...

    @abstractmethod
    def record_payment_event(
        self, session: Session, invoice: Invoice, actor: Persona, event_key: str, kind: str
    ) -> Invoice: ...


class MockPaymentProvider(PaymentProvider):
    def create_invoice(self, session, royalty):
        existing = session.scalar(select(Invoice).where(Invoice.royalty_id == royalty.id))
        if existing:
            return existing
        if royalty.status != "APPROVED" or Decimal(royalty.amount) <= 0:
            raise HTTPException(409, "Only an approved positive royalty can be invoiced.")
        studio = session.get(Persona, royalty.studio_id)
        invoice = Invoice(
            royalty_id=royalty.id,
            provider_id=f"SIMULATED-{uid()[:12].upper()}",
            artist_id=royalty.artist_id,
            studio_id=royalty.studio_id,
            recipient=studio.email,
            amount=royalty.amount,
            currency=royalty.currency,
        )
        session.add(invoice)
        session.flush()
        session.add(
            PaymentEvent(
                invoice_id=invoice.id,
                event_key=f"created_{invoice.id}",
                kind="CREATED",
                actor_id=royalty.artist_id,
            )
        )
        return invoice

    def get_invoice(self, session, invoice_id):
        invoice = session.get(Invoice, invoice_id)
        if not invoice:
            raise HTTPException(404, "Invoice not found.")
        return invoice

    def list_invoices(self, session, actor):
        owner = Invoice.artist_id if actor.role == "artist" else Invoice.studio_id
        return list(
            session.scalars(select(Invoice).where(owner == actor.id).order_by(Invoice.created_at.desc()))
        )

    def get_payment_status(self, session, invoice_id):
        return self.get_invoice(session, invoice_id).status

    def send_invoice(self, session, invoice, actor, event_key):
        return self.record_payment_event(session, invoice, actor, event_key, "SENT")

    def record_payment_event(self, session, invoice, actor, event_key, kind):
        existing = session.scalar(select(PaymentEvent).where(PaymentEvent.event_key == event_key))
        if existing:
            if existing.invoice_id != invoice.id or existing.kind != kind or existing.actor_id != actor.id:
                raise HTTPException(409, "Event key was already used for a different operation.")
            return invoice
        permitted = {("DRAFT", "SENT"), ("SENT", "PAID_SIMULATED")}
        if (invoice.status, kind) not in permitted:
            raise HTTPException(409, f"Cannot transition simulated invoice from {invoice.status} to {kind}.")
        if kind == "SENT" and actor.id != invoice.artist_id:
            raise HTTPException(403, "Only the artist can send this simulated invoice.")
        if kind == "PAID_SIMULATED" and actor.id != invoice.studio_id:
            raise HTTPException(403, "Switch to the assigned studio to simulate payment.")
        invoice.status = kind
        session.add(PaymentEvent(invoice_id=invoice.id, event_key=event_key, kind=kind, actor_id=actor.id))
        return invoice


from .paypal_provider import PayPalSandboxProvider  # noqa: E402
from .config import settings  # noqa: E402
from .paypal_client import SANDBOX_NOTICE  # noqa: E402


mock_provider = MockPaymentProvider()
sandbox_provider = PayPalSandboxProvider()


def provider_for(name):
    if name == "mock":
        return mock_provider
    if name == "paypal_sandbox":
        return sandbox_provider
    raise HTTPException(409, "Unsupported stored payment provider; no fallback is allowed.")


def payment_notice(invoice=None):
    selected = invoice.provider if invoice else settings.payment_provider
    return SANDBOX_NOTICE if selected == "paypal_sandbox" else PAYMENT_NOTICE


def settled_amount(db, invoice):
    if invoice.provider == "mock":
        return Decimal(invoice.amount) if invoice.status == "PAID_SIMULATED" else Decimal("0")
    if invoice.status not in {"PAID", "PARTIALLY_PAID", "REFUNDED", "PARTIALLY_REFUNDED"}:
        return Decimal("0")
    detail = db.scalar(select(SandboxInvoiceDetail).where(SandboxInvoiceDetail.invoice_id == invoice.id))
    if not detail:
        return Decimal("0")
    # Only actual PayPal payment rows count as received test funds; never external/manual marks.
    rows = [row for row in detail.transactions if row.get("type") == "PAYPAL" and row.get("payment_id")]
    try:
        paid = sum(
            (
                Decimal(row["amount"]["value"])
                for row in rows
                if row["amount"]["currency_code"] == invoice.currency
            ),
            Decimal("0"),
        )
        if (
            len({row["payment_id"] for row in rows}) != len(rows)
            or not paid.is_finite()
            or not 0 <= paid <= Decimal(invoice.amount)
        ):
            return Decimal("0")
        return max(Decimal("0"), paid - Decimal(detail.refunded_amount))
    except (KeyError, TypeError, ValueError, InvalidOperation):
        return Decimal("0")


def outstanding_amount(db, invoice):
    """Remaining invoice debt, distinct from net receipts after refunds."""
    if invoice.status in {"PAID_SIMULATED", "PAID", "CANCELLED", "REFUNDED"}:
        return Decimal("0")
    if invoice.provider == "paypal_sandbox":
        detail = db.scalar(select(SandboxInvoiceDetail).where(SandboxInvoiceDetail.invoice_id == invoice.id))
        if detail and detail.due_amount is not None:
            return Decimal(detail.due_amount)
    return max(Decimal("0"), Decimal(invoice.amount) - settled_amount(db, invoice))


class PaymentRouter:
    def create_invoice(self, session, royalty):
        return provider_for(settings.payment_provider).create_invoice(session, royalty)

    def list_invoices(self, session, actor):
        return mock_provider.list_invoices(session, actor)

    def send_invoice(self, session, invoice, actor, event_key):
        return provider_for(invoice.provider).send_invoice(session, invoice, actor, event_key)

    def get_invoice(self, session, invoice_id):
        return mock_provider.get_invoice(session, invoice_id)

    def get_payment_status(self, session, invoice_id):
        invoice = self.get_invoice(session, invoice_id)
        return provider_for(invoice.provider).get_payment_status(session, invoice_id)

    def record_payment_event(self, session, invoice, actor, event_key, kind):
        return provider_for(invoice.provider).record_payment_event(session, invoice, actor, event_key, kind)


provider = PaymentRouter()
