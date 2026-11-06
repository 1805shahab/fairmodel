from abc import ABC, abstractmethod
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import Invoice, PaymentEvent, Persona, Royalty, uid

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


class PayPalSandboxProvider(PaymentProvider):
    """Intentionally non-operational. No OAuth, HTTP calls or fabricated provider responses.

    Future adapter must map local approved royalties to Invoicing v2 with durable request IDs,
    verify webhook signatures, reconcile invoice amounts/currencies, and deduplicate event IDs.
    The manual simulate-payment route must remain mock-only when that adapter is enabled.
    """

    def __init__(self):
        raise NotImplementedError(
            "PayPal account access and explicit integration authorization are required."
        )

    def create_invoice(self, session, royalty):
        raise NotImplementedError

    def send_invoice(self, session, invoice, actor, event_key):
        raise NotImplementedError

    def get_invoice(self, session, invoice_id):
        raise NotImplementedError

    def list_invoices(self, session, actor):
        raise NotImplementedError

    def get_payment_status(self, session, invoice_id):
        raise NotImplementedError

    def record_payment_event(self, session, invoice, actor, event_key, kind):
        raise NotImplementedError


provider: PaymentProvider = MockPaymentProvider()
