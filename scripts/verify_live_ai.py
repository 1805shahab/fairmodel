"""Run real AI smoke checks on first-party samples without exposing credentials.

Run from backend/: .venv/Scripts/python.exe ../scripts/verify_live_ai.py
No demo AI fallback, database approvals, invoices, or payment calls are performed.
Only aggregate results are saved to ignored storage/live-ai-verification.json.
"""

import json
import logging
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

logging.disable(logging.CRITICAL)
PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "backend"))


def main() -> int:
    from fastapi import HTTPException
    from pypdf import PdfReader

    from app import ai, audio
    from app.config import settings

    summary = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "fixture_mode": False,
        "payment_calls": False,
        "configured": {
            "gemini": bool(settings.gemini_api_key.get_secret_value()),
            "groq": bool(settings.groq_api_key.get_secret_value()),
        },
        "checks": {},
    }
    print(json.dumps({"configured": summary["configured"]}), flush=True)
    fixtures = PROJECT / "backend" / "fixtures"
    if not all((fixtures / name).is_file() for name in ("sample-license.pdf", "sample-narration.wav")):
        print(json.dumps({"error": "Generate first-party sample files with scripts/create-demo.ps1 first."}))
        return 1

    def contract_check():
        if not summary["configured"]["gemini"]:
            raise HTTPException(503, "Gemini key is not configured.")
        path = fixtures / "sample-license.pdf"
        reader = PdfReader(path)
        pages = [{"page": i + 1, "text": page.extract_text() or ""} for i, page in enumerate(reader.pages)]
        return ai.extract_contract(path, pages, False)

    def audio_check():
        if not summary["configured"]["groq"]:
            raise HTTPException(503, "Groq key is not configured.")
        if not audio.availability()["ffmpeg"]:
            tools = list((PROJECT / "tools" / "ffmpeg-dist").glob("**/ffmpeg.exe"))
            if tools:
                settings.ffmpeg_binary = str(tools[0])
                settings.ffprobe_binary = str(tools[0].with_name("ffprobe.exe"))
        settings.storage_dir.mkdir(parents=True, exist_ok=True)
        original = fixtures / "sample-narration.wav"
        normalized = settings.storage_dir / "live-check-normalized.wav"
        metadata = audio.probe(original)
        audio.normalize(original, normalized)
        measurement = audio.speech_activity(normalized)
        result = ai.transcribe(normalized, original, False)
        if not result.get("transcript", "").strip():
            raise HTTPException(502, "Groq returned an empty transcript.")
        return metadata, measurement, result

    results = {}
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = {
            pool.submit(contract_check): "gemini_contract",
            pool.submit(audio_check): "groq_transcription",
        }
        for future in as_completed(futures):
            name = futures[future]
            try:
                value = future.result()
                results[name] = value
                if name == "gemini_contract":
                    terms, provider = value
                    check = {
                        "status": "passed",
                        "provider": provider,
                        "verified_citations": len(terms.evidence),
                        "review_flags": len(terms.ambiguities),
                        "unknown_fields": [
                            key for key in type(terms).model_fields if getattr(terms, key) is None
                        ],
                    }
                else:
                    metadata, measurement, transcript = value
                    check = {
                        "status": "passed",
                        "provider": transcript["provider"],
                        "duration_seconds": metadata["duration_seconds"],
                        "spoken_seconds": measurement["spoken_seconds"],
                        "transcript_characters": len(transcript["transcript"]),
                        "timestamp_segments": len(transcript["timestamps"]),
                    }
            except HTTPException as error:
                # Application messages are deliberately sanitized. Never print provider exception text.
                check = {"status": "failed", "http_status": error.status_code, "detail": error.detail}
            except Exception:
                check = {
                    "status": "failed",
                    "detail": "Local check failed. No private exception data displayed.",
                }
            summary["checks"][name] = check
            print(json.dumps({name: check}), flush=True)

    if len(results) == 2:
        try:
            terms, _ = results["gemini_contract"]
            transcript = results["groq_transcription"][2]["transcript"]
            findings, provider = ai.content_findings(terms, transcript, False)
            check = {
                "status": "passed",
                "provider": provider,
                "findings": len(findings.findings),
                "review_flags": len(findings.uncertainty),
            }
        except HTTPException as error:
            check = {"status": "failed", "http_status": error.status_code, "detail": error.detail}
        except Exception:
            check = {
                "status": "failed",
                "detail": "Content check failed. No private exception data displayed.",
            }
        summary["checks"]["gemini_content"] = check
        print(json.dumps({"gemini_content": check}), flush=True)

    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    (settings.storage_dir / "live-ai-verification.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    return (
        0
        if len(summary["checks"]) == 3
        and all(check["status"] == "passed" for check in summary["checks"].values())
        else 1
    )


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        print(
            json.dumps(
                {
                    "error": "Configuration or startup failed. Check backend settings locally; no secret values displayed."
                }
            )
        )
        raise SystemExit(1) from None
