"""Measure original stock-TTS audio. Optional live AI smoke; never attest, allocate or invoice."""

import argparse
import hashlib
import json
import logging
import sys
from pathlib import Path

logging.disable(logging.CRITICAL)
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))


def main():
    from app import ai, audio
    from app.config import settings
    from app.royalties import calculate
    from pypdf import PdfReader

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live-ai", action="store_true")
    args = parser.parse_args()
    probes = list((ROOT / "tools" / "ffmpeg-dist").glob("**/ffprobe.exe"))
    if probes:
        settings.ffprobe_binary = str(probes[0])
        settings.ffmpeg_binary = str(probes[0].with_name("ffmpeg.exe"))
    directory = ROOT / "backend" / "fixtures" / "paypal-sandbox-demo"
    original = directory / "original-harbor-lamp-ad.wav"
    normalized = directory / "normalized.wav"
    metadata = audio.probe(original)
    audio.normalize(original, normalized)
    measurement = audio.speech_activity(normalized)
    result = {
        "fictional_stock_tts": True,
        "artist_attestation": False,
        "invoice_created": False,
        "sha256": hashlib.sha256(original.read_bytes()).hexdigest(),
        "metadata": metadata,
        "measurement": measurement,
    }
    if args.live_ai:
        pdf = ROOT / "backend" / "fixtures" / "sample-license.pdf"
        pages = [
            {"page": i + 1, "text": page.extract_text() or ""}
            for i, page in enumerate(PdfReader(pdf).pages)
        ]
        terms, contract_provider = ai.extract_contract(pdf, pages, False)
        transcript = ai.transcribe(normalized, original, False)
        content, content_provider = ai.content_findings(
            terms, transcript["transcript"], False
        )
        result.update(
            contract_provider=contract_provider,
            contract_terms=terms.model_dump(mode="json"),
            transcription=transcript,
            content=content.model_dump(mode="json"),
            content_provider=content_provider,
        )
        if measurement["spoken_seconds"] is not None:
            from decimal import Decimal

            result["conditional_sample_calculation"] = calculate(
                terms, Decimal(measurement["spoken_seconds"])
            )
    (directory / "measurement.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "audio_prepared": True,
                "total_seconds": metadata["duration_seconds"],
                "spoken_seconds": measurement["spoken_seconds"],
                "live_ai_requested": args.live_ai,
                "live_ai_completed": bool(result.get("transcription")),
                "conditional_sample_amount": result.get(
                    "conditional_sample_calculation", {}
                ).get("amount"),
                "artist_review_still_required": True,
                "invoice_created": False,
            }
        )
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001 - CLI boundary must never print secret-bearing provider/config exceptions.
        print(
            json.dumps(
                {
                    "error": "Preparation or requested live provider check failed; no fixture fallback, approvals or invoices were created. Inspect runtime integration settings and retry."
                }
            )
        )
        raise SystemExit(1) from None
