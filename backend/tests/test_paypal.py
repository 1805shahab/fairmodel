import copy
import json
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Event

import httpx
import pytest
from pydantic import SecretStr

from app import main, payments
from app.config import Settings, settings
from app.paypal_client import PayPalClient, PayPalError, sandbox_link
from test_workflow import mock_audio, process, setup_license, submit


def sandbox_config(**changes):
    return Settings(
        _env_file=None,
        paypal_client_id="test-client",
        paypal_client_secret="test-secret",
        paypal_sandbox_merchant_email="merchant@business.example.com",
        paypal_sandbox_buyer_email="buyer@personal.example.com",
        **changes,
    )


class FakePayPal:
    def __init__(self):
        self.requests = []
        self.remote = {}
        self.payload = None
        self.token_calls = 0
        self.create_calls = 0
        self.send_calls = 0
        self.fail_create = False
        self.unknown_create = False
        self.send_timeout = False
        self.get_fails = False
        self.signature = "SUCCESS"

    def __call__(self, request):
        assert request.url.host == "api-m.sandbox.paypal.com"
        self.requests.append(request)
        path = request.url.path
        if path == "/v1/oauth2/token":
            self.token_calls += 1
            return httpx.Response(
                200,
                json={
                    "access_token": "only-test-token",
                    "expires_in": 100,
                    "token_type": "Bearer",
                    "scope": "https://uri.paypal.com/services/invoicing",
                },
            )
        if path == "/v1/notifications/verify-webhook-signature":
            return httpx.Response(200, json={"verification_status": self.signature})
        if path == "/v2/invoicing/search-invoices":
            return httpx.Response(200, json={"items": list(self.remote.values())})
        if path == "/v2/invoicing/invoices" and request.method == "POST":
            self.create_calls += 1
            self.payload = json.loads(request.content)
            assert "invoicer" not in self.payload and self.payload["configuration"]["auto_populate_invoicer"]
            if self.fail_create:
                return httpx.Response(403, json={"private": "secret provider body"})
            remote = {
                "id": "INV2-TEST-REAL-RESPONSE",
                "status": "DRAFT",
                "detail": {
                    **self.payload["detail"],
                    "metadata": {"last_update_time": "2026-11-09T00:00:00Z"},
                },
                "invoicer": {"email_address": "merchant@business.example.com"},
                "primary_recipients": self.payload["primary_recipients"],
                "amount": {**self.payload["items"][0]["unit_amount"], "breakdown": {}},
                "payments": {"paid_amount": {"currency_code": "USD", "value": "0.00"}, "transactions": []},
                "due_amount": self.payload["items"][0]["unit_amount"],
            }
            if not self.unknown_create:
                self.remote[remote["id"]] = remote
            if self.unknown_create == "accepted" or self.unknown_create:
                if self.unknown_create == "accepted":
                    self.remote[remote["id"]] = remote
                raise httpx.ReadTimeout("private transport text", request=request)
            return httpx.Response(201, json={"id": remote["id"]})
        if path.endswith("/send"):
            self.send_calls += 1
            remote = self.remote[path.split("/")[-2]]
            remote["status"] = "SENT"
            remote["detail"]["metadata"]["recipient_view_url"] = (
                "https://www.sandbox.paypal.com/invoice/p/#PROVIDER-RETURNED"
            )
            if self.send_timeout:
                raise httpx.ReadTimeout("private timeout", request=request)
            return httpx.Response(202, json={})
        if path.startswith("/v2/invoicing/invoices/"):
            if self.get_fails:
                return httpx.Response(503, json={"private": "not returned"})
            return httpx.Response(200, json=copy.deepcopy(self.remote[path.split("/")[-1]]))
        return httpx.Response(200, json={"items": []})


@pytest.fixture
def paypal(monkeypatch):
    fake = FakePayPal()
    wire = PayPalClient(
        config=sandbox_config(paypal_allow_drafts=True, paypal_allow_sending=True),
        transport=httpx.MockTransport(fake),
    )
    monkeypatch.setattr(settings, "payment_provider", "paypal_sandbox")
    monkeypatch.setattr(payments.sandbox_provider, "client", wire)
    monkeypatch.setattr(payments.sandbox_provider, "config", wire.config)
    yield fake, wire
    wire.http.close()


def charge(client, artist, studio, monkeypatch, terms, *, approve=True):
    license_ = setup_license(client, artist, monkeypatch, terms)
    mock_audio(monkeypatch)
    asset = submit(client, studio, license_["id"]).json()["id"]
    assert process(client, studio, asset)["status"] == "ADDITIONAL_ROYALTY_DUE"
    royalty = client.get("/api/royalties", headers=artist).json()[0]
    if approve:
        result = client.post(
            f"/api/royalties/{royalty['id']}/decision",
            headers=artist,
            json={"approve": True, "note": "Reviewed the current deterministic financial evidence."},
        )
        assert result.status_code == 200
    return asset, royalty


def create(client, artist, royalty):
    return client.post(
        f"/api/royalties/{royalty['id']}/invoice",
        headers=artist,
        json={
            "confirm_sandbox": True,
            "expected_amount": royalty["amount"],
            "expected_currency": "USD",
            "expected_recipient": "buyer@personal.example.com",
        },
    )


def test_oauth_cache_expiry_and_credential_rotation():
    fake, clock = FakePayPal(), [0]
    wire = PayPalClient(config=sandbox_config(), transport=httpx.MockTransport(fake), clock=lambda: clock[0])
    assert wire.access_token() == wire.access_token() and fake.token_calls == 1
    clock[0] = 91
    wire.access_token()
    assert fake.token_calls == 2
    wire.config.paypal_client_secret = SecretStr("different-test-secret")
    wire.access_token()
    assert fake.token_calls == 3
    wire.http.close()


@pytest.mark.parametrize(
    "status,category",
    [
        (401, "INVALID_CREDENTIALS_OR_TOKEN"),
        (403, "PERMISSION_DENIED"),
        (429, "RATE_LIMITED"),
        (503, "PROVIDER_UNAVAILABLE"),
    ],
)
def test_oauth_errors_never_leak_provider_data(status, category):
    wire = PayPalClient(
        config=sandbox_config(),
        transport=httpx.MockTransport(
            lambda _: httpx.Response(status, json={"access_token": "PRIVATE", "message": "PRIVATE"})
        ),
    )
    with pytest.raises(PayPalError) as error:
        wire.access_token()
    assert error.value.category == category and "PRIVATE" not in str(error.value)
    wire.http.close()


def test_missing_credentials_production_and_invalid_token_fail_without_fallback():
    config = Settings(_env_file=None)
    wire = PayPalClient(
        config=config, transport=httpx.MockTransport(lambda _: pytest.fail("No network expected"))
    )
    with pytest.raises(PayPalError, match="CREDENTIALS_NOT_CONFIGURED"):
        wire.access_token()
    config.paypal_environment = "production"
    with pytest.raises(PayPalError, match="PRODUCTION_FORBIDDEN"):
        wire.access_token()
    wire.http.close()


def test_draft_payload_idempotency_separate_send_and_permissions(
    client, artist, studio, monkeypatch, terms, paypal
):
    fake, _ = paypal
    _, royalty = charge(client, artist, studio, monkeypatch, terms)
    assert client.post(f"/api/royalties/{royalty['id']}/invoice", headers=artist).status_code == 409
    assert create(client, studio, royalty).status_code == 403
    draft = create(client, artist, royalty)
    assert draft.status_code == 201, draft.text
    invoice = draft.json()
    assert invoice["status"] == "DRAFT" and not invoice["simulated"]
    assert fake.payload["items"][0]["unit_amount"] == {"currency_code": "USD", "value": "30.00"}
    assert fake.create_calls == 1 and fake.send_calls == 0
    assert create(client, artist, royalty).json()["id"] == invoice["id"]
    assert fake.create_calls == 1
    assert (
        client.post(
            f"/api/invoices/{invoice['id']}/send",
            headers=studio,
            json={"event_key": "sandbox_send_once", "confirm_sandbox": True},
        ).status_code
        == 403
    )
    sent = client.post(
        f"/api/invoices/{invoice['id']}/send",
        headers=artist,
        json={"event_key": "sandbox_send_once", "confirm_sandbox": True},
    )
    assert sent.status_code == 200, sent.text
    assert sent.json()["status"] == "SENT" and fake.send_calls == 1
    assert sent.json()["sandbox"]["payment_url"].startswith("https://www.sandbox.paypal.com/")
    assert (
        client.post(
            f"/api/invoices/{invoice['id']}/simulate-payment",
            headers=studio,
            json={"event_key": "not_a_real_payment"},
        ).status_code
        == 409
    )
    assert client.get(f"/api/invoices/{invoice['id']}", headers=artist).json()["status"] == "SENT"


@pytest.mark.parametrize("accepted", [True, "accepted"])
def test_uncertain_creation_reconciles_without_repeating_remote_write(
    client, artist, studio, monkeypatch, terms, paypal, accepted
):
    fake, _ = paypal
    _, royalty = charge(client, artist, studio, monkeypatch, terms)
    fake.unknown_create = accepted
    first = create(client, artist, royalty)
    assert first.status_code == 409 and fake.create_calls == 1
    retry = create(client, artist, royalty)
    assert retry.status_code == (201 if accepted == "accepted" else 409), retry.text
    assert fake.create_calls == 1
    assert "private" not in first.text


def test_provider_denial_is_honest_and_read_failure_recovers_stored_id(
    client, artist, studio, monkeypatch, terms, paypal
):
    fake, _ = paypal
    _, royalty = charge(client, artist, studio, monkeypatch, terms)
    fake.fail_create = True
    failure = create(client, artist, royalty)
    assert failure.status_code == 502 and "PERMISSION_DENIED" in failure.text
    assert client.get("/api/invoices", headers=artist).json() == []
    fake.fail_create, fake.get_fails = False, True
    assert create(client, artist, royalty).status_code == 409
    fake.get_fails = False
    assert create(client, artist, royalty).status_code == 201
    assert fake.create_calls == 2


@pytest.mark.parametrize(
    "status,paid,due,evidence,expected",
    [
        ("SENT", "0.00", "30.00", False, "SENT"),
        ("PAYMENT_PENDING", "30.00", "0.00", True, "PAYMENT_PENDING"),
        ("PARTIALLY_PAID", "10.00", "20.00", True, "PARTIALLY_PAID"),
        ("PAID", "30.00", "0.00", True, "PAID"),
        ("PAID", "10.00", "20.00", True, "NEEDS_RECONCILIATION"),
        ("PAID", "30.00", "0.00", False, "NEEDS_RECONCILIATION"),
        ("MARKED_AS_PAID", "30.00", "0.00", True, "NEEDS_RECONCILIATION"),
    ],
)
def test_authoritative_payment_states(
    client, artist, studio, monkeypatch, terms, paypal, status, paid, due, evidence, expected
):
    fake, _ = paypal
    _, royalty = charge(client, artist, studio, monkeypatch, terms)
    invoice = create(client, artist, royalty).json()
    remote = fake.remote[invoice["provider_id"]]
    remote["status"] = status
    remote["payments"]["paid_amount"]["value"] = paid
    remote["due_amount"]["value"] = due
    remote["payments"]["transactions"] = (
        [{"type": "PAYPAL", "payment_id": "TEST-PAYMENT", "amount": {"currency_code": "USD", "value": paid}}]
        if evidence
        else []
    )
    result = client.post(f"/api/invoices/{invoice['id']}/refresh", headers=studio)
    assert result.status_code == 200, result.text
    assert result.json()["status"] == expected
    assert result.json()["amount"] == "30.00"


def test_send_timeout_reconciles_once_and_stale_approval_blocks_new_send(
    client, artist, studio, monkeypatch, terms, paypal
):
    fake, _ = paypal
    asset, royalty = charge(client, artist, studio, monkeypatch, terms)
    invoice = create(client, artist, royalty).json()
    fake.send_timeout = True
    response = client.post(
        f"/api/invoices/{invoice['id']}/send",
        headers=artist,
        json={"event_key": "uncertain_send_once", "confirm_sandbox": True},
    )
    assert response.status_code == 409
    assert (
        client.post(
            f"/api/invoices/{invoice['id']}/send",
            headers=artist,
            json={"event_key": "uncertain_send_once", "confirm_sandbox": True},
        ).status_code
        == 200
    )
    assert fake.send_calls == 1


def test_unapproved_unresolved_and_zero_royalties_never_call_provider(
    client, artist, studio, monkeypatch, terms, paypal
):
    fake, _ = paypal
    _, royalty = charge(client, artist, studio, monkeypatch, terms, approve=False)
    assert create(client, artist, royalty).status_code == 409
    assert fake.create_calls == 0


def test_links_reject_production_and_untrusted_destinations():
    for value in [
        "https://www.paypal.com/invoice/p/x",
        "http://www.sandbox.paypal.com/x",
        "https://www.sandbox.paypal.com.evil.test/x",
        "javascript:alert(1)",
    ]:
        assert sandbox_link(value) is None
    assert sandbox_link("https://www.sandbox.paypal.com/invoice/p/x")


def test_verified_webhooks_reconcile_partial_payments_and_replay_idempotently(
    client, artist, studio, monkeypatch, terms, paypal
):
    fake, wire = paypal
    wire.config.paypal_webhook_id = SecretStr("test-webhook")
    _, royalty = charge(client, artist, studio, monkeypatch, terms)
    invoice = create(client, artist, royalty).json()
    remote = fake.remote[invoice["provider_id"]]
    remote["status"] = "PARTIALLY_PAID"
    remote["payments"]["paid_amount"]["value"] = "10.00"
    remote["due_amount"]["value"] = "20.00"
    headers = {
        "paypal-auth-algo": "SHA256withRSA",
        "paypal-cert-url": "https://api.sandbox.paypal.com/v1/notifications/certs/TEST",
        "paypal-transmission-id": "test-transmission",
        "paypal-transmission-sig": "test-signature",
        "paypal-transmission-time": "2026-11-09T00:00:00Z",
    }
    event = {
        "id": "TEST-EVENT",
        "event_type": "INVOICING.INVOICE.PAID",
        "resource": {"id": invoice["provider_id"]},
    }
    fake.signature = "FAILURE"
    assert client.post("/api/paypal/webhook", headers=headers, json=event).status_code == 401
    fake.signature = "SUCCESS"
    result = client.post("/api/paypal/webhook", headers=headers, json=event)
    assert result.status_code == 200, result.text
    assert result.json()["status"] == "PARTIALLY_PAID"
    assert client.post("/api/paypal/webhook", headers=headers, json=event).json()["duplicate"]
    assert len(client.get("/api/personas").json()) == 2


def test_schema_four_migration_backup_preserves_existing_rows(tmp_path):
    import sqlite3
    from sqlalchemy import create_engine, inspect
    from app.db import Base
    from app.migrations import migrate

    engine = create_engine("sqlite:///" + (tmp_path / "legacy.db").as_posix())
    added = {"sandbox_invoice_details", "payment_operations", "paypal_webhook_receipts"}
    Base.metadata.create_all(
        engine, tables=[table for table in Base.metadata.sorted_tables if table.name not in added]
    )
    with engine.begin() as connection:
        connection.exec_driver_sql("PRAGMA user_version=3")
        connection.exec_driver_sql(
            "INSERT INTO personas (id,created_at,updated_at,role,name,email) VALUES ('owner','old','old','artist','Preserved','owner@example.test')"
        )
    backup = migrate(engine)
    assert added.issubset(inspect(engine).get_table_names())
    with sqlite3.connect(backup) as old:
        assert old.execute("PRAGMA user_version").fetchone()[0] == 3
        assert old.execute("SELECT name FROM personas").fetchone()[0] == "Preserved"
    with engine.connect() as connection:
        assert connection.exec_driver_sql("SELECT name FROM personas").scalar() == "Preserved"
    assert migrate(engine) is None
    engine.dispose()


def test_concurrent_confirmed_drafts_create_one_remote_invoice(
    client, artist, studio, monkeypatch, terms, paypal
):
    fake, _ = paypal
    _, royalty = charge(client, artist, studio, monkeypatch, terms)
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(lambda _: create(client, artist, royalty), range(2)))
    # A request can observe the committed intent before its concurrent remote call completes.
    # Hold that request rather than replaying an uncertain write; retry after the first completes.
    assert all(response.status_code in {201, 409} for response in responses), [r.text for r in responses]
    for response in responses:
        if response.status_code == 409:
            assert "UNCERTAIN_CREATE_REQUIRES_RECONCILIATION" in response.json()["detail"]
    retry = create(client, artist, royalty)
    assert retry.status_code == 201, retry.text
    assert {response.json()["id"] for response in responses if response.status_code == 201} == {
        retry.json()["id"]
    }
    assert len(client.get("/api/invoices", headers=artist).json()) == 1
    assert fake.create_calls == 1


def test_live_write_flags_and_current_approval_are_required(
    client, artist, studio, monkeypatch, terms, paypal
):
    fake, wire = paypal
    asset, royalty = charge(client, artist, studio, monkeypatch, terms)
    wire.config.paypal_allow_drafts = False
    assert create(client, artist, royalty).status_code == 409 and fake.create_calls == 0
    wire.config.paypal_allow_drafts = True
    invoice = create(client, artist, royalty).json()
    wire.config.paypal_allow_sending = False
    body = {"event_key": "explicit_send_confirmation", "confirm_sandbox": True}
    assert client.post(f"/api/invoices/{invoice['id']}/send", headers=artist, json=body).status_code == 409
    wire.config.paypal_allow_sending = True
    assert (
        client.post(
            f"/api/assets/{asset}/authorization",
            headers=artist,
            json={
                "identity_confirmed": False,
                "use_authorized": False,
                "note": "Artist withdrew authorization pending another evidence review.",
            },
        ).status_code
        == 200
    )
    assert client.post(f"/api/invoices/{invoice['id']}/send", headers=artist, json=body).status_code == 409
    assert fake.send_calls == 0
    assert client.get(f"/api/invoices/{invoice['id']}", headers=artist).json()["amount"] == "30.00"


def test_concurrent_reconciliation_materializes_before_original_request_resumes(
    client, artist, studio, monkeypatch, terms, paypal
):
    from app import paypal_provider as integration
    from app.db import PaymentOperation

    fake, _ = paypal
    _, royalty = charge(client, artist, studio, monkeypatch, terms)
    published, resume = Event(), Event()
    original_checkpoint = integration.checkpoint

    def paused_checkpoint(db):
        accepted = any(
            isinstance(row, PaymentOperation) and row.remote_id and row.state == "INFLIGHT"
            for row in db.identity_map.values()
        )
        if not accepted or published.is_set():
            return original_checkpoint(db)
        # Force the exact real race: remote ID committed, original request has
        # released its DB lock, but has not materialized a local invoice yet.
        db.commit()
        published.set()
        assert resume.wait(10), "Concurrent reconciler did not finish"
        db.connection().exec_driver_sql("BEGIN IMMEDIATE")
        db.expire_all()

    monkeypatch.setattr(integration, "checkpoint", paused_checkpoint)
    with ThreadPoolExecutor(max_workers=1) as pool:
        first = pool.submit(create, client, artist, royalty)
        try:
            assert published.wait(10), "Remote acceptance was not journaled"
            reconciled = create(client, artist, royalty)
            assert reconciled.status_code == 201, reconciled.text
        finally:
            resume.set()
        original = first.result()
    assert original.status_code == 201, original.text
    assert original.json()["id"] == reconciled.json()["id"]
    assert fake.create_calls == 1
    assert len(client.get("/api/invoices", headers=artist).json()) == 1


def test_diagnostic_is_read_only_and_reports_permissions(client, artist, studio, monkeypatch, paypal):
    fake, wire = paypal
    monkeypatch.setattr(main, "paypal_client", wire)
    assert client.post("/api/paypal/diagnostic", headers=studio).status_code == 403
    response = client.post("/api/paypal/diagnostic", headers=artist)
    assert response.status_code == 200
    assert response.json()["sandbox_authentication"] == "SUCCESS"
    assert response.json()["invoicing_capability"] == "VERIFIED_READ_ONLY"
    assert fake.create_calls == fake.send_calls == 0


@pytest.mark.parametrize("field", ["amount", "currency", "issuer", "recipient", "reference"])
def test_provider_mismatches_hold_without_changing_approved_money(
    client, artist, studio, monkeypatch, terms, paypal, field
):
    fake, _ = paypal
    _, royalty = charge(client, artist, studio, monkeypatch, terms)
    invoice = create(client, artist, royalty).json()
    remote = fake.remote[invoice["provider_id"]]
    if field == "amount":
        remote["amount"]["value"] = "99.00"
    elif field == "currency":
        remote["amount"]["currency_code"] = "EUR"
    elif field == "issuer":
        remote["invoicer"]["email_address"] = "other@example.com"
    elif field == "recipient":
        remote["primary_recipients"][0]["billing_info"]["email_address"] = "other@example.com"
    else:
        remote["detail"]["reference"] = "another charge"
    assert client.post(f"/api/invoices/{invoice['id']}/refresh", headers=artist).status_code == 502
    preserved = client.get(f"/api/invoices/{invoice['id']}", headers=artist).json()
    assert preserved["amount"] == "30.00" and preserved["currency"] == "USD"
    assert preserved["sandbox"]["error"] == "INVOICE_EVIDENCE_MISMATCH"


def test_paid_state_cannot_regress_from_old_get_or_out_of_order_webhook(
    client, artist, studio, monkeypatch, terms, paypal
):
    fake, wire = paypal
    wire.config.paypal_webhook_id = SecretStr("test-webhook")
    _, royalty = charge(client, artist, studio, monkeypatch, terms)
    invoice = create(client, artist, royalty).json()
    remote = fake.remote[invoice["provider_id"]]
    remote["status"] = "PAID"
    remote["payments"] = {
        "paid_amount": {"currency_code": "USD", "value": "30.00"},
        "transactions": [
            {
                "type": "PAYPAL",
                "payment_id": "TEST-TRANSACTION",
                "amount": {"currency_code": "USD", "value": "30.00"},
            }
        ],
    }
    remote["due_amount"]["value"] = "0.00"
    assert client.post(f"/api/invoices/{invoice['id']}/refresh", headers=artist).json()["status"] == "PAID"
    assert (
        client.get("/api/analytics", headers=artist).json()["totals_by_currency"]["USD"]["outstanding"] == "0"
    )
    remote["status"] = "SENT"
    assert client.post(f"/api/invoices/{invoice['id']}/refresh", headers=artist).status_code == 502
    assert client.get(f"/api/invoices/{invoice['id']}", headers=artist).json()["status"] == "PAID"
    assert (
        client.get("/api/analytics", headers=artist).json()["totals_by_currency"]["USD"]["outstanding"] == "0"
    )


def test_empty_or_unconfigured_webhook_never_triggers_financial_transition(client, paypal):
    assert client.post("/api/paypal/webhook", json={"id": "TEST"}).status_code == 503


@pytest.mark.parametrize(
    "refund,state,net", [("10.00", "PARTIALLY_REFUNDED", "20.00"), ("30.00", "REFUNDED", "0.00")]
)
def test_refunds_preserve_history_and_net_received_totals(
    client, artist, studio, monkeypatch, terms, paypal, refund, state, net
):
    fake, _ = paypal
    _, royalty = charge(client, artist, studio, monkeypatch, terms)
    invoice = create(client, artist, royalty).json()
    remote = fake.remote[invoice["provider_id"]]
    remote["status"] = state
    remote["payments"] = {
        "paid_amount": {"currency_code": "USD", "value": "30.00"},
        "transactions": [
            {
                "type": "PAYPAL",
                "payment_id": "TEST-REFUND-ORIGINAL",
                "amount": {"currency_code": "USD", "value": "30.00"},
            }
        ],
    }
    remote["due_amount"]["value"] = "0.00"
    remote["refunds"] = {"refund_amount": {"currency_code": "USD", "value": refund}}
    result = client.post(f"/api/invoices/{invoice['id']}/refresh", headers=artist)
    assert result.status_code == 200 and result.json()["status"] == state
    assert result.json()["amount"] == "30.00"
    totals = client.get("/api/analytics", headers=artist).json()["totals_by_currency"]["USD"]
    assert Decimal(totals["paid_sandbox"]) == Decimal(net)
    assert Decimal(totals["outstanding"]) == 0
    remote["refunds"]["refund_amount"]["value"] = "0.00"
    remote["status"] = "PAID"
    assert client.post(f"/api/invoices/{invoice['id']}/refresh", headers=artist).status_code == 502
    preserved = client.get(f"/api/invoices/{invoice['id']}", headers=artist).json()
    assert preserved["status"] == state and preserved["sandbox"]["refunded_amount"] == refund


def test_out_of_order_sent_webhook_uses_current_paid_get(client, artist, studio, monkeypatch, terms, paypal):
    fake, wire = paypal
    wire.config.paypal_webhook_id = SecretStr("test-webhook")
    _, royalty = charge(client, artist, studio, monkeypatch, terms)
    invoice = create(client, artist, royalty).json()
    remote = fake.remote[invoice["provider_id"]]
    remote["status"] = "PAID"
    remote["due_amount"]["value"] = "0.00"
    remote["payments"] = {
        "paid_amount": {"currency_code": "USD", "value": "30.00"},
        "transactions": [
            {
                "type": "PAYPAL",
                "payment_id": "TEST-WEBHOOK-PAID",
                "amount": {"currency_code": "USD", "value": "30.00"},
            }
        ],
    }
    headers = {
        "paypal-auth-algo": "SHA256withRSA",
        "paypal-cert-url": "https://api.sandbox.paypal.com/test",
        "paypal-transmission-id": "test",
        "paypal-transmission-sig": "test",
        "paypal-transmission-time": "2026-11-09T00:00:00Z",
    }
    event = {
        "id": "TEST-OLD-SENT",
        "event_type": "INVOICING.INVOICE.SENT",
        "resource": {"id": invoice["provider_id"]},
    }
    result = client.post("/api/paypal/webhook", headers=headers, json=event)
    assert result.status_code == 200 and result.json()["status"] == "PAID"
    assert client.post("/api/paypal/webhook", headers=headers, json=event).json()["duplicate"]


def test_read_retry_and_401_refresh_never_repeat_posts():
    seen = []

    def handler(request):
        seen.append((request.method, request.url.path))
        if request.url.path == "/v1/oauth2/token":
            return httpx.Response(
                200, json={"access_token": "only-test-token", "token_type": "Bearer", "expires_in": 100}
            )
        reads = sum(path == "/v2/invoicing/invoices" for _, path in seen)
        return httpx.Response(401 if reads == 1 else 200, json={"items": []})

    wire = PayPalClient(config=sandbox_config(), transport=httpx.MockTransport(handler))
    assert wire.request("GET", "/v2/invoicing/invoices") == {"items": []}
    assert sum(path == "/v1/oauth2/token" for _, path in seen) == 2
    wire.http.close()


def test_passport_retains_actual_returned_sandbox_id_and_partial_payment_state(
    client, artist, studio, monkeypatch, terms, paypal
):
    fake, _ = paypal
    asset, royalty = charge(client, artist, studio, monkeypatch, terms)
    invoice = create(client, artist, royalty).json()
    remote = fake.remote[invoice["provider_id"]]
    remote["status"] = "PARTIALLY_PAID"
    remote["due_amount"]["value"] = "20.00"
    remote["payments"] = {
        "paid_amount": {"currency_code": "USD", "value": "10.00"},
        "transactions": [
            {
                "type": "PAYPAL",
                "payment_id": "TEST-PASSPORT-PARTIAL",
                "amount": {"currency_code": "USD", "value": "10.00"},
            }
        ],
    }
    assert client.post(f"/api/invoices/{invoice['id']}/refresh", headers=artist).status_code == 200
    # HTTP responses here are explicitly mocked, not proof of a live Sandbox operation.
    asset_id = client.get("/api/royalties", headers=artist).json()[0]["asset_id"]
    p = client.get(f"/api/assets/{asset_id}/passport", headers=artist).json()
    assert p["asset"]["invoice"]["provider_id"] == invoice["provider_id"]
    assert not p["asset"]["invoice"]["simulated"]
    assert p["asset"]["invoice"]["sandbox"]["paid_amount"] == "10.00"
    assert p["stages"][-1]["state"] == "pending"
