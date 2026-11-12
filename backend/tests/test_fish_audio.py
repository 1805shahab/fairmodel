"""Real local WAV/FFmpeg checks; generated tones only, Fish HTTP always mocked."""

import hashlib
import io
import json
import struct
import wave

import httpx
import pytest

from app import audio, fish_generation
from app.config import settings
from app.fish_audio import FishAudioFailure, inspect_wav, normalize_output
from test_fish_generation import mocked_http, fish_case


def sample(rate=44100, channels=1, bits=16, floating=False, streaming=False, extensible=False, frames=None):
    tag = 3 if floating else 1
    if floating:
        value = struct.pack("<f" if bits == 32 else "<d", 0.15)
    else:
        value = b"\x80" if bits == 8 else (1000).to_bytes(bits // 8, "little", signed=True)
    raw = value * channels * (rate // 2 if frames is None else frames)
    alignment = channels * bits // 8
    fmt = struct.pack(
        "<HHIIHH", 0xFFFE if extensible else tag, channels, rate, rate * alignment, alignment, bits
    )
    if extensible:
        fmt += struct.pack("<HHI", 22, bits, 3 if channels == 2 else 4)
        fmt += struct.pack("<I", tag) + b"\x00\x00\x10\x00\x80\x00\x00\xaa\x00\x38\x9b\x71"
    chunks = b"fmt " + struct.pack("<I", len(fmt)) + fmt
    chunks += b"data" + struct.pack("<I", 0xFFFFFFFF if streaming else len(raw)) + raw
    if len(raw) % 2:
        chunks += b"\x00"
    size = 0xFFFFFFFF if streaming else len(chunks) + 4
    return b"RIFF" + struct.pack("<I", size) + b"WAVE" + chunks


@pytest.mark.parametrize(
    "options",
    [
        {},
        {"rate": 48000, "channels": 2},
        {"rate": 16000},
        {"bits": 8},
        {"bits": 24},
        {"bits": 32},
        {"bits": 32, "floating": True},
        {"bits": 64, "floating": True},
        {"extensible": True},
        {"extensible": True, "bits": 32, "floating": True},
        {"streaming": True},
        {"streaming": True, "rate": 24000},
    ],
)
def test_valid_provider_variants_normalize_with_actual_ffmpeg(monkeypatch, tmp_path, options):
    monkeypatch.setattr(settings, "storage_dir", tmp_path)
    incoming = sample(**options)
    result, receipt = normalize_output(incoming, "variant")
    with wave.open(io.BytesIO(result), "rb") as wav:
        assert (wav.getframerate(), wav.getnchannels(), wav.getsampwidth()) == (24000, 1, 2)
        assert wav.getnframes() / 24000 == pytest.approx(0.5, abs=0.001)
        assert len(wav.readframes(wav.getnframes())) == wav.getnframes() * 2
    assert receipt["normalization_applied"]
    assert receipt["received_audio"]["sample_rate"] == options.get("rate", 44100)
    assert receipt["provider_audio_sha256"] == hashlib.sha256(incoming).hexdigest()
    assert list(tmp_path.iterdir()) == []
    if options.get("streaming"):
        assert "cannot prove" in receipt["stream_length_note"]


def test_canonical_wav_passes_without_reencoding(monkeypatch):
    monkeypatch.setattr(audio, "run", lambda *args: pytest.fail("Canonical WAV should not invoke FFmpeg"))
    original = sample(rate=24000)
    result, receipt = normalize_output(original, "canonical")
    assert result == original and not receipt["normalization_applied"]


@pytest.mark.parametrize("declared", [0, 36, 100, 4000000])
def test_stale_outer_size_with_complete_finite_data_is_repaired(monkeypatch, tmp_path, declared):
    monkeypatch.setattr(settings, "storage_dir", tmp_path)
    received = bytearray(sample(rate=24000))
    struct.pack_into("<I", received, 4, declared)
    result, receipt = normalize_output(bytes(received), "outer")
    facts = receipt["received_audio"]
    assert facts["length_mode"] == "outer_size_repaired"
    assert facts["declared_riff_size"] == declared
    assert facts["observed_data_bytes"] == facts["declared_data_size"]
    with wave.open(io.BytesIO(result), "rb") as wav:
        assert wav.getnframes() == 12000
        assert wav.readframes(12000) == bytes(received[44:])
    assert receipt["normalization_applied"] and list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("rate", [24000, 44100])
def test_legacy_empty_stream_header_uses_observed_samples_with_uncertainty(monkeypatch, tmp_path, rate):
    monkeypatch.setattr(settings, "storage_dir", tmp_path)
    received = bytearray(sample(rate=rate))
    struct.pack_into("<I", received, 4, 36)
    struct.pack_into("<I", received, 40, 0)
    result, receipt = normalize_output(bytes(received), "legacy")
    facts = receipt["received_audio"]
    assert facts["length_mode"] == "legacy_empty_stream"
    assert facts["declared_data_size"] == 0 and facts["observed_data_bytes"] == len(received) - 44
    assert "cannot prove" in receipt["stream_length_note"]
    with wave.open(io.BytesIO(result), "rb") as wav:
        assert wav.getnframes() / wav.getframerate() == pytest.approx(0.5, abs=0.001)
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    "kind",
    [
        "finite_truncated",
        "finite_oversized_data",
        "short_data_extra_bytes",
        "fake_zero_header",
        "legacy_incomplete_frame",
    ],
)
def test_outer_repair_never_expands_truncated_finite_data(monkeypatch, kind):
    received = bytearray(sample(rate=24000))
    struct.pack_into("<I", received, 4, 36)
    if kind == "finite_truncated":
        received = received[:-20]
    elif kind == "finite_oversized_data":
        struct.pack_into("<I", received, 40, len(received) * 2)
    elif kind == "short_data_extra_bytes":
        struct.pack_into("<I", received, 40, 4)
    elif kind == "fake_zero_header":
        # A zero data marker outside the narrow legacy empty-WAV layout is invalid.
        struct.pack_into("<I", received, 4, 100)
        struct.pack_into("<I", received, 40, 0)
    elif kind == "legacy_incomplete_frame":
        struct.pack_into("<I", received, 40, 0)
        received = received[:-1]
    monkeypatch.setattr(audio, "run", lambda *args: pytest.fail("No decoder for inconsistent inner frames"))
    with pytest.raises(FishAudioFailure) as caught:
        normalize_output(bytes(received), "unsafe")
    facts = caught.value.diagnostic["received_audio"]
    assert facts["declared_riff_size"] == 36 or kind == "fake_zero_header"
    assert "declared_data_size" in facts
    assert facts["sample_rate"] == 24000


def test_stale_outer_size_preserves_valid_metadata_chunks(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "storage_dir", tmp_path)
    received = bytearray(sample(rate=24000))
    received += b"JUNK" + struct.pack("<I", 4) + b"test"
    # The outer size still describes the original WAV without the metadata.
    result, receipt = normalize_output(bytes(received), "metadata")
    assert receipt["received_audio"]["length_mode"] == "outer_size_repaired"
    assert receipt["received_audio"]["sample_frames"] == 12000
    with wave.open(io.BytesIO(result), "rb") as wav:
        assert wav.getnframes() == 12000  # JUNK never becomes billable samples.


def test_mocked_http_legacy_stream_at_reported_response_size(monkeypatch, tmp_path):
    # Reproduce the observed byte count using synthetic PCM. The historical
    # response's header/samples were not retained; this is not a reconstruction.
    received = bytearray(sample(rate=24000, frames=1048728))
    assert len(received) == 2097500
    struct.pack_into("<I", received, 4, 36)
    struct.pack_into("<I", received, 40, 0)
    calls = []

    def handler(request):
        calls.append(request)
        assert request.headers["model"] == "s2.1-pro-free"
        return httpx.Response(200, content=bytes(received))

    mocked_http(monkeypatch, tmp_path, handler)
    result, receipt = fish_generation.synthesize(
        tmp_path / "reference", "Test reference.", "Test script.", "large"
    )
    assert len(calls) == 1
    assert receipt["audio_processing"]["received_audio"]["response_bytes"] == 2097500
    with wave.open(io.BytesIO(result), "rb") as wav:
        assert wav.getnframes() == 1048728
        assert wav.getnframes() / wav.getframerate() == pytest.approx(43.697)
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    "kind",
    [
        "not_wav",
        "json",
        "empty",
        "truncated",
        "truncated_chunk",
        "odd_frame",
        "bad_rate",
        "compressed",
        "bad_byte_rate",
        "unknown_riff_only",
        "nan_float",
        "too_short",
    ],
)
def test_invalid_audio_rejected_before_decoder(monkeypatch, kind):
    data = bytearray(sample())
    if kind == "not_wav":
        data = b"private malformed audio content"
    elif kind == "json":
        data = b'{"error":"private-provider-body secret-token"}'
    elif kind == "empty":
        data = b""
    elif kind == "truncated":
        data = data[:-20]
    elif kind == "truncated_chunk":
        data = data[:-20]
        struct.pack_into("<I", data, 4, len(data) - 8)
    elif kind == "odd_frame":
        data = sample(streaming=True)[:-1]
    elif kind == "bad_rate":
        struct.pack_into("<I", data, 24, 0)
    elif kind == "compressed":
        struct.pack_into("<H", data, 20, 6)
    elif kind == "bad_byte_rate":
        struct.pack_into("<I", data, 28, 1)
    elif kind == "unknown_riff_only":
        struct.pack_into("<I", data, 4, 0xFFFFFFFF)
    elif kind == "nan_float":
        data = bytearray(sample(bits=32, floating=True))
        struct.pack_into("<f", data, 44, float("nan"))
    elif kind == "too_short":
        data = bytearray(sample(rate=24000)[:48])
        struct.pack_into("<I", data, 4, len(data) - 8)
        struct.pack_into("<I", data, 40, 4)
    monkeypatch.setattr(audio, "run", lambda *args: pytest.fail("Malformed audio must not reach decoder"))
    with pytest.raises(FishAudioFailure) as caught:
        normalize_output(bytes(data), "bad")
    assert caught.value.diagnostic["audio_accepted"] is False
    assert "private" not in caught.value.detail + json.dumps(caught.value.diagnostic)


def test_normalization_failure_cleans_private_temporaries(monkeypatch, tmp_path):
    from fastapi import HTTPException

    monkeypatch.setattr(settings, "storage_dir", tmp_path)

    def fail(*args):
        raise HTTPException(422, "private decoder output")

    monkeypatch.setattr(audio, "run", fail)
    with pytest.raises(FishAudioFailure) as caught:
        normalize_output(sample(), "failed")
    assert caught.value.diagnostic["category"] == "LOCAL_NORMALIZATION_FAILED"
    assert "private" not in caught.value.detail and list(tmp_path.iterdir()) == []


def test_mocked_http_normalizes_provider_output_and_persists_real_format_facts(monkeypatch, tmp_path):
    incoming = sample(rate=44100, streaming=True)
    calls = []

    def handler(request):
        calls.append(request)
        assert request.headers["model"] == "s2.1-pro-free"
        return httpx.Response(200, content=incoming)

    mocked_http(monkeypatch, tmp_path, handler)
    data, receipt = fish_generation.synthesize(
        tmp_path / "reference", "Test transcript.", "Test script.", "wire"
    )
    assert len(calls) == 1 and receipt["provider_http_status"] == 200
    assert receipt["audio_sha256"] == hashlib.sha256(data).hexdigest()
    assert receipt["audio_processing"]["received_audio"]["sample_rate"] == 44100
    assert receipt["audio_processing"]["received_audio"]["length_mode"] == "streaming_unknown"


def test_local_audio_failure_keeps_diagnostic_without_success_or_replay(
    client, artist, studio, monkeypatch, terms
):
    _, _, _, body = fish_case(client, artist, studio, monkeypatch, terms)

    def fail(*args):
        try:
            inspect_wav(b"private nonaudio data")
        except FishAudioFailure as error:
            raise error

    monkeypatch.setattr(fish_generation, "synthesize", fail)
    assert client.post("/api/generations", headers=studio, json=body).status_code == 502
    saved = client.get("/api/generations", headers=studio).json()[0]
    receipt = saved["receipt"]
    assert saved["status"] == "FAILED" and saved["asset_id"] is None
    assert receipt["failure"]["provider_http_status"] == 200
    assert receipt["failure"]["category"] == "NON_WAV_RESPONSE"
    assert receipt["failure"]["received_audio"]["response_bytes"] == 21
    assert "succeeded_at" not in receipt and "private nonaudio" not in json.dumps(receipt)
    monkeypatch.setattr(fish_generation, "synthesize", lambda *args: pytest.fail("Never replay failed job"))
    assert client.post("/api/generations", headers=studio, json=body).json()["id"] == saved["id"]
    assert client.get("/api/royalties", headers=artist).json() == []


def test_mocked_provider_variant_is_saved_as_normalized_uploaded_asset(
    client, artist, studio, monkeypatch, terms, tmp_path
):
    _, _, _, body = fish_case(client, artist, studio, monkeypatch, terms)
    received = sample(rate=44100, channels=2, bits=32, floating=True)
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(200, content=received)

    mocked_http(monkeypatch, tmp_path, handler)
    response = client.post("/api/generations", headers=studio, json=body)
    assert response.status_code == 201, response.text
    saved = response.json()
    assert saved["status"] == "SUCCEEDED" and len(calls) == 1
    facts = saved["receipt"]["audio_processing"]
    assert facts["received_audio"]["sample_rate"] == 44100
    assert facts["received_audio"]["encoding"] == "ieee_float"
    assert facts["normalization_applied"]
    asset = client.get(f"/api/assets/{saved['asset_id']}", headers=studio).json()
    assert asset["status"] == "UPLOADED" and asset["analysis"] is None
    assert asset["authorization_state"] == "unresolved"
    assert client.get("/api/royalties", headers=artist).json() == []
    assert client.get("/api/invoices", headers=artist).json() == []
