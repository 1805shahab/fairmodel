"""Explicit read-only Sandbox diagnostic; never creates/sends invoices or payments."""

import argparse
import json
import logging
import sys
from pathlib import Path

logging.disable(logging.CRITICAL)
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--capability",
        action="store_true",
        help="Also read the invoice listing (no writes).",
    )
    options = parser.parse_args()
    try:
        from app.paypal_client import paypal_client

        result = paypal_client.diagnostic(options.capability)
        print(json.dumps(result))
        raise SystemExit(
            0
            if result["sandbox_authentication"] == "SUCCESS"
            and (
                not options.capability
                or result["invoicing_capability"] == "VERIFIED_READ_ONLY"
            )
            else 1
        )
    except Exception:  # noqa: BLE001 - CLI boundary must never print secret-bearing configuration exceptions.
        print(
            json.dumps(
                {
                    "error_category": "LOCAL_CONFIGURATION_ERROR",
                    "detail": "No credential values or private exception details displayed.",
                }
            )
        )
        raise SystemExit(1) from None
