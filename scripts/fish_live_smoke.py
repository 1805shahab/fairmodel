"""Manual, one-request Fish smoke test through FairModel. Dry-run by default."""

import argparse
import json
from pathlib import Path

import httpx


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--grant-id", required=True)
    parser.add_argument("--script-file", type=Path, required=True)
    parser.add_argument("--campaign-file", type=Path, required=True)
    parser.add_argument(
        "--request-key",
        required=True,
        help="Reuse the same key to retrieve this request, never replay it.",
    )
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--confirm-private-audio-transfer", action="store_true")
    parser.add_argument("--confirm-free-tier-terms", action="store_true")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("Invalid local backend port.")
    script = args.script_file.read_text(encoding="utf-8").strip()
    campaign = json.loads(args.campaign_file.read_text(encoding="utf-8"))
    if not 10 <= len(script) <= 4000 or not isinstance(campaign, dict):
        parser.error("Use a 10–4,000 character script and a campaign JSON object.")
    if not args.execute:
        print(
            "DRY RUN: no HTTP request or recording transfer. Review the Fish-specific artist grant, actual script/campaign, free-tier terms and retention before executing."
        )
        return
    if not args.confirm_private_audio_transfer or not args.confirm_free_tier_terms:
        parser.error(
            "Live execution requires both explicit transfer and free-tier terms acknowledgments."
        )
    # Application rechecks ownership, immutable license scope, provider consent,
    # free model, and request-key idempotency. No direct Fish/profile/payment call.
    try:
        with httpx.Client(timeout=180, follow_redirects=False) as client:
            response = client.post(
                f"http://127.0.0.1:{args.port}/api/generations",
                headers={"X-Demo-Persona": "studio_demo"},
                json={
                    "provider": "fish",
                    "grant_id": args.grant_id,
                    "request_key": args.request_key,
                    "script": script,
                    "campaign": campaign,
                    "confirm_provider_use": True,
                },
            )
        if response.status_code not in (200, 201):
            print(
                f"FairModel rejected/failed the operation (HTTP {response.status_code}). Inspect saved generation history in the app; no response body or credentials printed."
            )
            return 1
        data = response.json()
        print(
            json.dumps(
                {key: data.get(key) for key in ("id", "provider", "status", "asset_id")}
            )
        )
        return 0 if data.get("status") == "SUCCEEDED" else 1
    except (httpx.HTTPError, ValueError):
        print(
            "Local request failed or timed out. The remote outcome may be unknown; inspect history and reuse this request key. No automatic retry was attempted."
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
