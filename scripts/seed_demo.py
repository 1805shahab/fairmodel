"""Idempotent fictional judging scenarios through the real local application endpoints.

Run from backend/. All AI choices are explicit fixtures; audio/PDF processing is real.
Only records in this dedicated fixture bundle are scripted. No external services or payments.
"""

import json
import logging
import sys
from pathlib import Path

from fastapi.testclient import TestClient

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "backend"))
logging.disable(logging.CRITICAL)


def seed_scenarios(client):
    from app.evidence import digest

    fixtures = PROJECT / "backend" / "fixtures"
    bundle = json.loads((fixtures / "scenarios.json").read_text(encoding="utf-8"))
    if any(not case.get("sha256") for case in bundle["cases"]):
        raise RuntimeError("Finalize the scenario fixtures first.")
    title = "Judging scenarios — OFFLINE FIXTURES v1 — " + digest(bundle)[:12]
    artist = {"X-Demo-Persona": "artist_demo"}
    studio = {"X-Demo-Persona": "studio_demo"}

    def request(method, path, actor=artist, **kwargs):
        response = client.request(method, "/api" + path, headers=actor, **kwargs)
        if response.status_code >= 400:
            raise RuntimeError(
                f"Local demo endpoint failed: {path}, HTTP {response.status_code}."
            )
        return response.json()

    if request("GET", "/integrations")["payment_provider"] != "mock":
        raise RuntimeError(
            "Fixture seeding is mock-only. No Sandbox invoice or simulated attestation was created."
        )
    # API listing makes this work with either the normal DB or test dependency overrides.
    existing = next(
        (row for row in request("GET", "/licenses") if row["title"] == title), None
    )
    license_ = existing or request(
        "POST", "/licenses", json={"title": title, "studio_id": "studio_demo"}
    )
    lid = license_["id"]
    if not license_["contract_hash"]:
        license_ = request(
            "POST",
            f"/licenses/{lid}/contract",
            files={
                "file": (
                    "sample-license.pdf",
                    (fixtures / "sample-license.pdf").read_bytes(),
                    "application/pdf",
                )
            },
        )
    if license_["contract_hash"] != bundle["contract_sha256"]:
        raise RuntimeError(
            "Existing demo license source differs. No approved source was overwritten."
        )
    if license_["status"] != "ACTIVE":
        if license_["extraction_provider"] == "not_run":
            license_ = request(
                "POST", f"/licenses/{lid}/extract", json={"use_demo_fixture": True}
            )
        license_ = request(
            "POST",
            f"/licenses/{lid}/approve",
            json={
                "terms": license_["terms"],
                "expected_version": license_["version"],
                "note": "Scripted fixture-only artist contract review for fictional judging scenarios.",
            },
        )
    outcomes = []
    for case in bundle["cases"]:
        if case["id"] not in {"A", "B", "C"}:
            continue
        metadata = {
            "name": f"Judging scenario {case['id']} — explicit offline fixture",
            "region": "US",
            "medium": "online advertising",
            "language": "English",
            "category": "political advertising"
            if case["id"] == "C"
            else "consumer products",
            "generation_provider": "Windows stock TTS — fictional demonstration",
            "intended_use_date": "2026-11-09",
        }
        asset = request(
            "POST",
            "/assets",
            studio,
            data={"license_id": lid, "campaign": json.dumps(metadata)},
            files={
                "file": (
                    case["file"],
                    (fixtures / case["file"]).read_bytes(),
                    "audio/wav",
                )
            },
        )
        aid = asset["id"]
        if asset["campaign"] != metadata:
            raise RuntimeError(
                "Existing demo campaign was edited. It was preserved; review it manually."
            )
        detail = request("GET", f"/assets/{aid}")
        if not detail.get("analysis"):
            request(
                "POST",
                f"/assets/{aid}/analyze",
                studio,
                json={"use_demo_fixture": True},
            )
        elif not detail["analysis"]["result"].get("demo_fixture"):
            raise RuntimeError(
                "Existing demo asset was reanalyzed live. Its provenance was preserved."
            )
        if not detail.get("authorization"):
            request(
                "POST",
                f"/assets/{aid}/authorization",
                json={
                    "identity_confirmed": True,
                    "use_authorized": case["id"] != "C",
                    "note": "OFFLINE FIXTURE EXERCISE ONLY: scripted fictional artist attestation. No real identity or permission is claimed.",
                },
            )
        result = request(
            "POST", f"/assets/{aid}/evaluate", studio, json={"use_demo_fixture": True}
        )["result"]
        expected = {
            "A": "COMPLIANT",
            "B": "ADDITIONAL_ROYALTY_DUE",
            "C": "RESTRICTED_USAGE",
        }[case["id"]]
        if result["status"] != expected:
            raise RuntimeError(
                f"Scenario {case['id']} requires manual review; existing records were not reset."
            )
        invoice = None
        if case["id"] == "B":
            detail = request("GET", f"/assets/{aid}")
            royalty = detail["royalty"]
            if royalty["status"] == "PENDING" or (
                royalty["status"] == "APPROVED" and not royalty["approval_current"]
            ):
                request(
                    "POST",
                    f"/royalties/{royalty['id']}/decision",
                    json={
                        "approve": True,
                        "note": "Scripted fixture-only financial approval after measured usage and eligibility checks.",
                    },
                )
            invoice = request("POST", f"/royalties/{royalty['id']}/invoice")
        outcomes.append(
            {
                "scenario": case["id"],
                "asset_id": aid,
                "status": result["status"],
                "spoken_seconds": result["calculation"]["spoken_seconds"],
                "additional_royalty": result["calculation"]["amount"],
                "invoice_id": invoice["id"] if invoice else None,
                "simulated": True,
            }
        )
    return {
        "mode": "EXPLICIT OFFLINE FIXTURES",
        "license_id": lid,
        "scenarios": outcomes,
        "notice": "SIMULATED PAYMENT — NO REAL FUNDS TRANSFERRED",
    }


def main():
    from app.config import settings
    from app.main import app

    probes = list((PROJECT / "tools" / "ffmpeg-dist").glob("**/ffprobe.exe"))
    if probes:
        settings.ffprobe_binary = str(probes[0])
        settings.ffmpeg_binary = str(probes[0].with_name("ffmpeg.exe"))
    with TestClient(app) as client:
        result = seed_scenarios(client)
    print(json.dumps(result))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001 -- never expose private configuration/provider exception details
        # Endpoint paths/statuses are local and safe; never print raw provider exceptions.
        print(
            "Demo seeding failed; inspect local fixture availability, application state and tests. No private exception details displayed."
        )
        raise SystemExit(1) from None
