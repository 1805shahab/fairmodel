import json
import shutil
import subprocess
import wave
from decimal import Decimal
from pathlib import Path

import webrtcvad
from fastapi import HTTPException

from .config import settings


def run(command: list[str], timeout: int = 60) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            command,
            capture_output=True,
            timeout=timeout,
            check=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except FileNotFoundError:
        raise HTTPException(
            503, "FFmpeg/ffprobe is unavailable. Set backend FFMPEG_BINARY and FFPROBE_BINARY."
        ) from None
    except (subprocess.SubprocessError, OSError):
        raise HTTPException(
            422, "Audio decoding failed or timed out. Upload a valid WAV, MP3 or M4A audio file."
        ) from None


def probe(path: Path) -> dict:
    data = json.loads(
        run(
            [
                settings.ffprobe_binary,
                "-v",
                "error",
                "-protocol_whitelist",
                "file,pipe",
                "-show_format",
                "-show_streams",
                "-of",
                "json",
                str(path),
            ]
        ).stdout
    )
    streams = data.get("streams", [])
    audio = [x for x in streams if x.get("codec_type") == "audio"]
    if len(audio) != 1 or any(x.get("codec_type") == "video" for x in streams):
        raise HTTPException(422, "Upload a single-track audio file without video.")
    formats = set(data.get("format", {}).get("format_name", "").split(","))
    if not formats.intersection({"wav", "mp3", "m4a", "mov"}):
        raise HTTPException(422, "The file content is not WAV, MP3 or M4A.")
    try:
        duration = Decimal(str(data["format"]["duration"]))
        rate = int(audio[0]["sample_rate"])
    except (KeyError, ValueError):
        raise HTTPException(422, "Audio duration/sample rate could not be determined.") from None
    if not duration.is_finite() or not Decimal("0.1") <= duration <= settings.max_audio_seconds:
        raise HTTPException(422, f"Audio must be between 0.1 and {settings.max_audio_seconds} seconds.")
    if audio[0].get("channels", 0) > 2:
        raise HTTPException(422, "Only mono or stereo audio is supported.")
    return {
        "duration_seconds": str(duration.quantize(Decimal("0.001"))),
        "format": data["format"]["format_name"],
        "codec": audio[0]["codec_name"],
        "sample_rate": rate,
        "channels": audio[0]["channels"],
    }


def normalize(path: Path, output: Path):
    run(
        [
            settings.ffmpeg_binary,
            "-nostdin",
            "-v",
            "error",
            "-y",
            "-protocol_whitelist",
            "file,pipe",
            "-i",
            str(path),
            "-map",
            "0:a:0",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-c:a",
            "pcm_s16le",
            str(output),
        ]
    )
    if output.stat().st_size > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(422, "Normalized audio exceeds the provider upload limit.")


def speech_activity(path: Path) -> dict:
    try:
        with wave.open(str(path), "rb") as audio:
            if (audio.getnchannels(), audio.getsampwidth(), audio.getframerate()) != (1, 2, 16000):
                raise ValueError("Expected 16kHz mono PCM16")
            pcm = audio.readframes(audio.getnframes())
        detector = webrtcvad.Vad(2)
        frame_bytes = 960  # 30 milliseconds, 16kHz, signed 16-bit mono.
        activity = [
            detector.is_speech(pcm[i : i + frame_bytes], 16000)
            for i in range(0, len(pcm) - frame_bytes + 1, frame_bytes)
        ]
        segments = []
        start = None
        for i, active in enumerate(activity + [False]):
            if active and start is None:
                start = i
            if not active and start is not None:
                segments.append({"start": round(start * 0.03, 3), "end": round(i * 0.03, 3)})
                start = None
        duration = Decimal(sum(activity)) * Decimal("0.03")
        return {
            "spoken_seconds": str(duration),
            "speech_segments": segments,
            "vad": "WebRTC VAD mode 2 / 30ms / 16kHz mono",
            "measurement_uncertain": duration == 0,
            "measurement_note": "Estimated speech activity, not diarization. Music/noise can affect VAD. "
            "Artist approval is required before any charge.",
        }
    except Exception:
        return {
            "spoken_seconds": None,
            "speech_segments": [],
            "vad": "failed",
            "measurement_uncertain": True,
            "measurement_note": "Speech duration unavailable; human review required.",
        }


def availability() -> dict:
    return {
        "ffmpeg": bool(shutil.which(settings.ffmpeg_binary)),
        "ffprobe": bool(shutil.which(settings.ffprobe_binary)),
    }
