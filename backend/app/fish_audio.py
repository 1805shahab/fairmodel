"""Inspect Fish WAV/MP3 framing before decoding; normalize genuine samples locally."""

import hashlib
import io
import json
import math
import struct
import wave

from fastapi import HTTPException

from . import audio
from .config import settings
from .fish_mp3 import inspect_mp3
from .voice_generation import validate_wav

UNKNOWN_LENGTH = 0xFFFFFFFF


def probe_mp3(path, facts):
    """Probe only a complete, frame-checked private file; retain format facts only."""
    try:
        result = audio.run(
            [
                settings.ffprobe_binary,
                "-v",
                "error",
                "-err_detect",
                "explode",
                "-protocol_whitelist",
                "file,pipe",
                "-f",
                "mp3",
                "-show_entries",
                "stream=codec_type,codec_name,sample_rate,channels:format=format_name,duration",
                "-of",
                "json",
                str(path),
            ]
        )
        document = json.loads(result.stdout)
        streams = document.get("streams", [])
        if (
            len(streams) != 1
            or streams[0].get("codec_type") != "audio"
            or streams[0].get("codec_name") != "mp3"
            or document.get("format", {}).get("format_name") != "mp3"
        ):
            raise ValueError("Unexpected stream/container")
        stream = streams[0]
        rate, channels = int(stream["sample_rate"]), int(stream["channels"])
        duration = float(document["format"]["duration"])
        if (
            rate != facts["sample_rate"]
            or channels != facts["channels"]
            or not math.isfinite(duration)
            or not 0.1 <= duration <= settings.max_audio_seconds
        ):
            raise ValueError("Invalid probed format")
    except HTTPException:
        raise FishAudioFailure("MP3_PROBE_FAILED", facts) from None
    except (ValueError, KeyError, TypeError, IndexError):
        raise FishAudioFailure("MP3_PROBE_INVALID", facts) from None
    return {
        "tool": "ffprobe",
        "format": "mp3",
        "codec": "mp3",
        "sample_rate": rate,
        "channels": channels,
        "duration_seconds": round(duration, 6),
    }


def container_signature(data):
    """Fixed labels only: never persist arbitrary provider text or sample bytes."""
    if data[:4] == b"RIFF":
        return "riff_wave" if data[8:12] == b"WAVE" else "riff_other"
    if data[:3] == b"ID3" or (len(data) >= 2 and data[0] == 255 and data[1] & 224 == 224):
        return "mp3"
    prefix = data[:64].lstrip()
    if prefix[:1] in (b"{", b"["):
        return "json"
    if prefix[:1] == b"<":
        return "markup"
    return "unknown" if data else "empty"


class FishAudioFailure(HTTPException):
    def __init__(self, category, metadata=None):
        # Only callers inside this module supply metadata: numeric format facts,
        # fixed enum labels and byte counts; never response bodies or filenames.
        self.diagnostic = {
            "stage": "output_audio_validation",
            "category": category,
            "provider_http_status": 200,
            "audio_accepted": False,
            "received_audio": metadata or {},
        }
        facts = metadata or {}
        summary = ", ".join(
            f"{label}={facts[key]}"
            for key, label in (
                ("sample_rate", "Hz"),
                ("channels", "channels"),
                ("bits_per_sample", "bits"),
            )
            if key in facts
        )
        detail = f"Fish Audio output failed local validation ({category})"
        reason = {
            "EMPTY_AUDIO": "empty provider response",
            "NON_WAV_RESPONSE": "unsupported output format; expected a framed WAV or MP3",
            "PROVIDER_NON_AUDIO_RESPONSE": "provider returned an error or unsupported streaming content type",
            "PROVIDER_ERROR_PAYLOAD": "provider returned an error document instead of audio",
            "LOCAL_NORMALIZATION_FAILED": "FFmpeg conversion or final audio validation failed; check local FFmpeg availability",
            "HTTP_LENGTH_MISMATCH": "HTTP body length differs from the declared length",
            "TRUNCATED_PROVIDER_RESPONSE": "HTTP stream ended before its transport framing completed",
            "INCOMPLETE_PROVIDER_RESPONSE": "HTTP audio transfer failed or timed out before completion",
            "MP3_PROBE_FAILED": "FFprobe could not validate the completed MP3; check local FFprobe availability and audio integrity",
            "MP3_PROBE_INVALID": "FFprobe did not confirm a supported single-track MP3 matching its frame headers",
        }.get(category)
        if reason:
            detail += f": {reason}"
        if summary:
            detail += f"; received {summary}"
        super().__init__(502, detail + ". No asset, fixture fallback or automatic retry was created.")


def inspect_wav(data):
    facts = {"response_bytes": len(data), "container_format": container_signature(data)}

    def reject(category):
        raise FishAudioFailure(category, facts.copy())

    if not data:
        reject("EMPTY_AUDIO")
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        reject("OUTPUT_TOO_LARGE")
    if len(data) < 12 or data[:4] != b"RIFF" or data[8:12] != b"WAVE":
        reject("NON_WAV_RESPONSE")
    riff_size = struct.unpack_from("<I", data, 4)[0]
    streaming = riff_size == UNKNOWN_LENGTH
    facts.update(declared_riff_size=riff_size, actual_riff_size=len(data) - 8)
    facts["length_mode"] = "streaming_unknown" if streaming else "declared"
    # The outer size is an index, not the sample count. Inspect every inner
    # chunk first: intact finite data can prove a stale outer size is repairable.
    outer_mismatch = not streaming and riff_size + 8 != len(data)
    fmt = None
    pcm = None
    position = 12
    unknown_data = False
    legacy_empty_header = False
    while position < len(data):
        if position + 8 > len(data):
            reject("TRUNCATED_CHUNK_HEADER")
        kind = data[position : position + 4]
        size = struct.unpack_from("<I", data, position + 4)[0]
        start = position + 8
        if kind == b"data":
            facts.update(declared_data_size=size, available_data_bytes=len(data) - start)
        # Older Fish streaming writers emitted Python's empty 44-byte PCM WAV
        # header, then samples. Accept only that exact layout, not arbitrary
        # zero chunk lengths or general truncated finite declarations.
        if (
            kind == b"data"
            and size == 0
            and riff_size == 36
            and start == 44
            and fmt is not None
            and fmt[0] == 1
            and fmt[1] == 1
            and fmt[3:] == (2, 16)
            and len(data) > 44
        ):
            legacy_empty_header = True
            unknown_data = True
            size = len(data) - start
            facts["length_mode"] = "legacy_empty_stream"
        if size == UNKNOWN_LENGTH:
            if kind != b"data" or not streaming:
                reject("INVALID_STREAMING_HEADER")
            size = len(data) - start
            unknown_data = True
        if start + size > len(data):
            facts.update(
                failed_chunk="data" if kind == b"data" else "fmt" if kind == b"fmt " else "other",
                chunk_offset=position,
                declared_chunk_size=size,
                available_chunk_bytes=len(data) - start,
            )
            reject("TRUNCATED_CHUNK")
        if kind == b"fmt ":
            if fmt is not None or pcm is not None or size < 16:
                reject("INVALID_FORMAT_CHUNK")
            tag, channels, rate, byte_rate, alignment, bits = struct.unpack_from("<HHIIHH", data, start)
            facts.update(sample_rate=rate, channels=channels, bits_per_sample=bits, format_tag=tag)
            if tag == 0xFFFE:
                extension_size = struct.unpack_from("<H", data, start + 16)[0] if size >= 18 else 0
                if size < 40 or not 22 <= extension_size <= size - 18:
                    reject("INVALID_EXTENSIBLE_FORMAT")
                valid_bits = struct.unpack_from("<H", data, start + 18)[0]
                subtype = data[start + 24 : start + 40]
                if (
                    subtype[4:] != b"\x00\x00\x10\x00\x80\x00\x00\xaa\x00\x38\x9b\x71"
                    or not 0 < valid_bits <= bits
                ):
                    reject("UNSUPPORTED_EXTENSIBLE_FORMAT")
                tag = int.from_bytes(subtype[:4], "little")
            if (
                tag not in (1, 3)
                or (tag == 1 and bits not in (8, 16, 24, 32))
                or (tag == 3 and bits not in (32, 64))
            ):
                reject("UNSUPPORTED_WAV_ENCODING")
            if channels not in (1, 2) or not 8000 <= rate <= 96000:
                reject("UNSUPPORTED_WAV_FORMAT")
            if alignment != channels * (bits // 8) or byte_rate != rate * alignment:
                reject("INCONSISTENT_WAV_FORMAT")
            fmt = tag, channels, rate, alignment, bits
        elif kind == b"data":
            if pcm is not None or fmt is None:
                reject("INVALID_DATA_CHUNK")
            pcm = memoryview(data)[start : start + size]
        position = start + size + (size % 2)
        if unknown_data:
            position = len(data)
        elif position > len(data):
            reject("MISSING_CHUNK_PADDING")
    if pcm is None or fmt is None or not len(pcm):
        reject("MISSING_AUDIO_SAMPLES")
    if not legacy_empty_header and streaming != unknown_data:
        reject("INCONSISTENT_STREAMING_LENGTHS")
    if outer_mismatch and not legacy_empty_header:
        # All finite chunks, their padding and the data payload reached their
        # declared ends. Only the outer container index is stale.
        facts["length_mode"] = "outer_size_repaired"
    tag, channels, rate, alignment, bits = fmt
    if len(pcm) % alignment:
        reject("INCOMPLETE_AUDIO_FRAME")
    frames = len(pcm) // alignment
    duration = frames / rate
    facts.update(
        sample_frames=frames,
        duration_seconds=round(duration, 6),
        encoding="pcm_integer" if tag == 1 else "ieee_float",
        observed_data_bytes=len(pcm),
    )
    if not 0.1 <= duration <= settings.max_audio_seconds:
        reject("AUDIO_DURATION_LIMIT")
    if tag == 3 and any(
        not math.isfinite(value[0]) for value in struct.iter_unpack("<f" if bits == 32 else "<d", pcm)
    ):
        reject("NONFINITE_AUDIO_SAMPLES")
    return facts


def normalize_output(data, work_id):
    signature = container_signature(data)
    if signature in {"json", "markup"}:
        raise FishAudioFailure(
            "PROVIDER_ERROR_PAYLOAD", {"response_bytes": len(data), "container_format": signature}
        )
    mp3 = signature == "mp3"
    if mp3:
        facts = {"response_bytes": len(data), "container_format": signature}

        def reject(category):
            raise FishAudioFailure(category, facts.copy())

        if len(data) > settings.max_upload_mb * 1024 * 1024:
            reject("OUTPUT_TOO_LARGE")
        facts = inspect_mp3(data, facts, reject)
        if not 0.1 <= facts["duration_seconds"] <= settings.max_audio_seconds:
            reject("AUDIO_DURATION_LIMIT")
    else:
        facts = inspect_wav(data)
    canonical = not mp3 and (
        facts["format_tag"],
        facts["channels"],
        facts["sample_rate"],
        facts["bits_per_sample"],
    ) == (
        1,
        1,
        24000,
        16,
    )
    changed = not canonical or facts["length_mode"] != "declared"
    probe = None
    if not changed:
        validate_wav(data, provider="Fish Audio")
        result = data
    else:
        source = settings.storage_dir / f"{work_id}-fish-response.{'mp3' if mp3 else 'wav'}"
        target = settings.storage_dir / f"{work_id}-fish-normalized.wav"
        try:
            source.write_bytes(data)
            if mp3:
                probe = probe_mp3(source, facts)
            # Seal only validated layouts using the observed HTTP payload.
            # Never expand a finite inner data length, invent samples or pad it.
            if not mp3 and facts["length_mode"] != "declared":
                sealed = bytearray(data)
                struct.pack_into("<I", sealed, 4, len(sealed) - 8)
                if facts["length_mode"] in {"streaming_unknown", "legacy_empty_stream"}:
                    pos = 12
                    while sealed[pos : pos + 4] != b"data":
                        length = struct.unpack_from("<I", sealed, pos + 4)[0]
                        pos += 8 + length + length % 2
                    struct.pack_into("<I", sealed, pos + 4, len(sealed) - pos - 8)
                source.write_bytes(sealed)
            audio.run(
                [
                    settings.ffmpeg_binary,
                    "-nostdin",
                    "-v",
                    "error",
                    "-xerror",
                    "-err_detect",
                    "explode",
                    "-y",
                    "-protocol_whitelist",
                    "file,pipe",
                    "-f",
                    "mp3" if mp3 else "wav",
                    "-i",
                    str(source),
                    "-map",
                    "0:a:0",
                    "-ac",
                    "1",
                    "-ar",
                    "24000",
                    "-c:a",
                    "pcm_s16le",
                    str(target),
                ]
            )
            if target.stat().st_size > settings.max_upload_mb * 1024 * 1024:
                raise FishAudioFailure("NORMALIZED_OUTPUT_TOO_LARGE", facts)
            result = target.read_bytes()
            inspect_wav(result)
            validate_wav(result, provider="Fish Audio")
            with wave.open(io.BytesIO(result), "rb") as wav:
                decoded_duration = wav.getnframes() / wav.getframerate()
                # MP3 priming and end padding may remove at most several frames.
                # A large mismatch still fails; never pad a shortened decode.
                tolerance = 4 * (1152 / facts["sample_rate"]) if mp3 else 0.002
                delta = facts["duration_seconds"] - decoded_duration
                if delta < -0.002 or delta > tolerance:
                    raise FishAudioFailure("NORMALIZATION_DURATION_MISMATCH", facts)
        except FishAudioFailure:
            raise
        except (HTTPException, OSError, wave.Error, EOFError):
            raise FishAudioFailure("LOCAL_NORMALIZATION_FAILED", facts) from None
        finally:
            source.unlink(missing_ok=True)
            target.unlink(missing_ok=True)
    with wave.open(io.BytesIO(result), "rb") as wav:
        output_facts = {
            "sample_rate": wav.getframerate(),
            "channels": wav.getnchannels(),
            "bits_per_sample": wav.getsampwidth() * 8,
            "sample_frames": wav.getnframes(),
            "duration_seconds": round(wav.getnframes() / wav.getframerate(), 6),
        }
    return result, {
        "received_audio": facts,
        "normalization_applied": changed,
        "provider_audio_sha256": hashlib.sha256(data).hexdigest(),
        "stored_audio_format": "WAV / PCM16 / mono / 24000 Hz",
        "normalized_audio": output_facts,
        "source_probe": probe,
        "stream_length_note": "Complete HTTP body and frame alignment verified; without a finite source length/index this cannot prove the provider's intended final duration."
        if facts["length_mode"] in {"streaming_unknown", "legacy_empty_stream", "unindexed_mp3"}
        else None,
    }
