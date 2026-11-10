"""Manually invoked local-API Sandbox test. Writes require per-case authorization arguments."""

import argparse
import json
import urllib.error
import urllib.request
from urllib.parse import urlparse


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="http://127.0.0.1:8000")
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--diagnose", action="store_true")
    actions.add_argument("--refresh", metavar="LOCAL_INVOICE_ID")
    actions.add_argument("--draft", metavar="ROYALTY_ID")
    actions.add_argument("--send", metavar="LOCAL_INVOICE_ID")
    parser.add_argument("--approve-amount")
    parser.add_argument("--approve-recipient")
    parser.add_argument("--i-authorize-this-sandbox-action", action="store_true")
    args = parser.parse_args()
    base = urlparse(args.base)
    if (
        base.scheme != "http"
        or base.hostname not in {"127.0.0.1", "localhost"}
        or base.username
        or base.password
    ):
        raise SystemExit("Only the local application API is supported.")

    def request(method, path, data=None):
        wire = urllib.request.Request(
            args.base.rstrip("/") + path,
            method=method,
            headers={
                "X-Demo-Persona": "artist_demo",
                "Content-Type": "application/json",
            },
            data=json.dumps(data or {}).encode() if method == "POST" else None,
        )
        try:
            with urllib.request.urlopen(wire, timeout=180) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            # App error bodies are sanitized; provider raw bodies/tokens are never returned.
            raise SystemExit(
                f"Application HTTP {error.code}. Inspect its UI for the safe error category."
            ) from None

    if args.diagnose:
        print(json.dumps(request("POST", "/api/paypal/diagnostic")))
        return
    if args.refresh:
        invoice = request("POST", f"/api/invoices/{args.refresh}/refresh")
    else:
        if (
            not args.i_authorize_this_sandbox_action
            or not args.approve_amount
            or not args.approve_recipient
        ):
            raise SystemExit(
                "No write performed. Supply the exact reviewed amount/recipient and explicit authorization flag."
            )
        if request("GET", "/health")["payment_provider"] != "paypal_sandbox":
            raise SystemExit("No write performed. Select paypal_sandbox explicitly.")
        if args.draft:
            preview = request("GET", f"/api/royalties/{args.draft}/invoice-preview")
            if (
                preview["amount"] != args.approve_amount
                or preview["sandbox_payload"]["buyer_email"] != args.approve_recipient
            ):
                raise SystemExit(
                    "No write performed. Preview differs from the authorized case."
                )
            invoice = request(
                "POST",
                f"/api/royalties/{args.draft}/invoice",
                {
                    "confirm_sandbox": True,
                    "expected_amount": args.approve_amount,
                    "expected_currency": preview["currency"],
                    "expected_recipient": args.approve_recipient,
                },
            )
        else:
            prior = request("GET", f"/api/invoices/{args.send}")
            if (
                prior["provider"] != "paypal_sandbox"
                or prior["amount"] != args.approve_amount
                or prior["recipient"] != args.approve_recipient
            ):
                raise SystemExit(
                    "No send performed. Stored invoice differs from the authorized case."
                )
            invoice = request(
                "POST",
                f"/api/invoices/{args.send}/send",
                {"event_key": "manual_send_" + args.send, "confirm_sandbox": True},
            )
    print(
        json.dumps(
            {
                key: invoice.get(key)
                for key in (
                    "id",
                    "provider",
                    "provider_id",
                    "amount",
                    "currency",
                    "status",
                    "notice",
                )
            }
        )
    )


if __name__ == "__main__":
    main()
