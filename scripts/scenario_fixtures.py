"""First-party offline judging fixtures; never overwrite existing fixture audio."""

import hashlib
import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT / "backend" / "fixtures"
sys.path.insert(0, str(PROJECT / "backend"))


def main():
    base = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    cases = [
        {
            "id": "A",
            "file": "scenario-included.wav",
            "type": "stock_tts",
            "transcript": "Explore the fictional Cedar stationery shop. Discover notebooks, pencils, and desk accessories for your next creative project. Browse the collection online today. This original synthetic example demonstrates included licensed usage.",
        },
        {
            "id": "B",
            "file": "sample-narration.wav",
            "type": "existing_stock_tts",
            "transcript": base["transcript"],
        },
        {
            "id": "C",
            "file": "scenario-restricted.wav",
            "type": "stock_tts",
            "transcript": "Vote for the fictional candidate in the imaginary Fairview election. This is a fictional political endorsement created solely for a software testing demonstration. No actual candidate or election is represented.",
            "prohibited_category": "political advertising",
        },
        {
            "id": "excerpt",
            "file": "scenario-excerpt.wav",
            "type": "excerpt",
            "transcript": " ".join(base["transcript"].split()[:36]),
            "source_file": "sample-narration.wav",
        },
    ]
    prior_path = ROOT / "scenarios.json"
    prior = (
        json.loads(prior_path.read_text(encoding="utf-8"))
        if prior_path.exists()
        else {}
    )
    for case in cases:
        old = next((c for c in prior.get("cases", []) if c["id"] == case["id"]), None)
        path = ROOT / case["file"]
        if (
            old
            and path.exists()
            and (
                (
                    old.get("sha256")
                    and old["sha256"] != hashlib.sha256(path.read_bytes()).hexdigest()
                )
                or old["transcript"] != case["transcript"]
            )
        ):
            raise RuntimeError(
                "Existing scenario input changed. Keep prior files for historical demos; generate a new bundle deliberately."
            )
        if old:
            case.update(
                {
                    key: old[key]
                    for key in ("sha256", "duration_seconds", "spoken_seconds")
                    if key in old
                }
            )
    if "--finalize" in sys.argv:
        from app import audio
        from app.config import settings

        probes = list((PROJECT / "tools" / "ffmpeg-dist").glob("**/ffprobe.exe"))
        if probes:
            settings.ffprobe_binary = str(probes[0])
            settings.ffmpeg_binary = str(probes[0].with_name("ffmpeg.exe"))
        excerpt = ROOT / "scenario-excerpt.wav"
        if not excerpt.exists():
            audio.run(
                [
                    settings.ffmpeg_binary,
                    "-nostdin",
                    "-v",
                    "error",
                    "-i",
                    str(ROOT / "sample-narration.wav"),
                    "-t",
                    "18",
                    "-ac",
                    "1",
                    "-ar",
                    "16000",
                    "-c:a",
                    "pcm_s16le",
                    str(excerpt),
                ]
            )
        for case in cases:
            path = ROOT / case["file"]
            normalized = ROOT / f"scenario-{case['id']}-normalized.wav"
            audio.normalize(path, normalized)
            measured = audio.speech_activity(normalized)
            case.update(
                {
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "duration_seconds": audio.probe(path)["duration_seconds"],
                    "spoken_seconds": measured["spoken_seconds"],
                }
            )
        if (
            not 0
            < float(cases[0]["spoken_seconds"])
            < 30
            < float(cases[1]["spoken_seconds"])
        ):
            raise RuntimeError(
                "Generated speech does not meet judging scenario A/B duration boundaries."
            )
    bundle = {
        "version": 1,
        "notice": "Explicit offline AI fixtures. Real local FFmpeg/VAD; Windows stock synthetic speech, not an artist voice clone.",
        "contract_sha256": base["contract_sha256"],
        "cases": cases,
    }
    prior_path.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    print(
        "First-party scenario specifications prepared."
        if "--finalize" not in sys.argv
        else json.dumps(
            {
                "fixture_bundle": "ready",
                "cases": [
                    {"id": c["id"], "spoken_seconds": c["spoken_seconds"]}
                    for c in cases
                ],
            }
        )
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001 -- never expose private configuration/provider exception details
        print(
            "Scenario preparation failed. Check local fixture/tool availability; private exception details omitted."
        )
        raise SystemExit(1) from None
