"""Mocked existing-draft repair, never live Sandbox writes."""

import copy
from contextlib import contextmanager

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app import payments
from app.db import Audit, Invoice, PaymentOperation, Report
from app.paypal_client import PayPalError
from app.paypal_reconciliation import ExistingInvoiceReads, reconcile_issuer
from test_paypal import charge, create
from test_voice_generation import session as session_generator

pytest_plugins = ["test_paypal"]
session = contextmanager(session_generator)


def prepare(client, artist, studio, monkeypatch, terms, paypal):
    fake, wire = paypal
    _, royalty = charge(client, artist, studio, monkeypatch, terms)
    wire.config.paypal_sandbox_merchant_email = "typo@business.example.com"
    response = create(client, artist, royalty)
    assert response.status_code == 409
    wire.config.paypal_sandbox_merchant_email = "merchant@business.example.com"
    with session() as db:
        operation = db.scalar(select(PaymentOperation).where(PaymentOperation.royalty_id == royalty["id"]))
        assert operation.state == "UNKNOWN" and operation.remote_id
        args = dict(
            operation_id=operation.id,
            remote_id=operation.remote_id,
            amount=royalty["amount"],
            currency="USD",
            recipient="buyer@personal.example.com",
            merchant="merchant@business.example.com",
            actor_id="artist_demo",
            note="Owner confirmed the correct merchant for this existing draft.",
        )
        original = copy.deepcopy(operation.payload)
    return args, original


def test_preview_execute_audit_idempotency_and_no_external_writes(
    client, artist, studio, monkeypatch, terms, paypal
):
    args, original = prepare(client, artist, studio, monkeypatch, terms, paypal)
    fake, _ = paypal
    marker = len(fake.requests)
    with session() as db:
        preview = reconcile_issuer(db, payments.sandbox_provider, **args)
        assert preview["status"] == "READY" and preview["provider_writes"] == 0
        assert not db.scalar(select(Invoice).where(Invoice.provider_id == args["remote_id"]))
        assert db.get(PaymentOperation, args["operation_id"]).payload == original
        db.rollback()
    with session() as db:
        result = reconcile_issuer(db, payments.sandbox_provider, **args, execute=True)
        db.commit()
        invoice_id = result["invoice_id"]
    with session() as db:
        invoice = db.get(Invoice, invoice_id)
        assert (
            invoice.provider_id == args["remote_id"] and invoice.status == "DRAFT" and not invoice.simulated
        )
        operation = db.get(PaymentOperation, args["operation_id"])
        assert operation.state == "SUCCEEDED" and operation.error is None
        assert operation.payload == {**original, "merchant_email": args["merchant"]}
        audits = list(db.scalars(select(Audit).where(Audit.action == "paypal.issuer_binding_corrected")))
        assert len(audits) == 1 and audits[0].detail["original_payload"] == original
        assert audits[0].detail["provider_writes"] == 0
        repeat = reconcile_issuer(db, payments.sandbox_provider, **args, execute=True)
        assert repeat["status"] == "ALREADY_RECONCILED" and repeat["invoice_id"] == invoice_id
    assert fake.create_calls == 1 and fake.send_calls == 0
    assert all(request.method == "GET" for request in fake.requests[marker:])


@pytest.mark.parametrize(
    "change",
    [
        "amount",
        "buyer",
        "merchant",
        "remote_id",
        "studio",
        "note",
        "credential",
        "stale",
        "sent",
        "reference",
        "remote_amount",
        "paid",
    ],
)
def test_ineligible_or_mismatching_reconciliation_preserves_hold(
    client, artist, studio, monkeypatch, terms, paypal, change
):
    args, original = prepare(client, artist, studio, monkeypatch, terms, paypal)
    fake, wire = paypal
    if change == "amount":
        args["amount"] = "999.00"
    elif change == "buyer":
        args["recipient"] = "another@personal.example.com"
    elif change == "merchant":
        args["merchant"] = "other@business.example.com"
    elif change == "remote_id":
        args["remote_id"] = "INV2-OTHER-INVOICE"
    elif change == "studio":
        args["actor_id"] = "studio_demo"
    elif change == "note":
        args["note"] = "short"
    elif change == "credential":
        from pydantic import SecretStr

        wire.config.paypal_client_id = SecretStr("another-test-app")
    elif change == "sent":
        fake.remote[args["remote_id"]]["status"] = "SENT"
    elif change == "reference":
        fake.remote[args["remote_id"]]["detail"]["reference"] = "other-royalty"
    elif change == "remote_amount":
        fake.remote[args["remote_id"]]["amount"]["value"] = "999.00"
    elif change == "paid":
        fake.remote[args["remote_id"]]["payments"]["paid_amount"]["value"] = "1.00"
    elif change == "stale":
        with session() as db:
            report = db.scalar(select(Report))
            report.result = {**report.result, "input_hash": "changed"}
            db.commit()
    with session() as db:
        with pytest.raises((HTTPException, PayPalError)):
            reconcile_issuer(db, payments.sandbox_provider, **args, execute=True)
        db.rollback()
    with session() as db:
        operation = db.get(PaymentOperation, args["operation_id"])
        assert operation.payload == original and operation.state == "UNKNOWN"
        assert not db.scalar(select(Invoice).where(Invoice.royalty_id == operation.royalty_id))
        assert not db.scalar(select(Audit).where(Audit.action == "paypal.issuer_binding_corrected"))
    assert fake.create_calls == 1 and fake.send_calls == 0


@pytest.mark.parametrize(
    "method,path",
    [
        ("POST", "/v2/invoicing/invoices"),
        ("POST", "/v2/invoicing/invoices/INV2-TEST/send"),
        ("GET", "/v2/invoicing/invoices/INV2-OTHER"),
    ],
)
def test_reconciliation_transport_cannot_write_or_read_other_invoice(method, path):
    with pytest.raises(HTTPException):
        ExistingInvoiceReads(None, "INV2-TEST").request(method, path)
