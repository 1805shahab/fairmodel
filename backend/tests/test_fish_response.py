"""Synthetic audio and mocked HTTP only; no private samples or live Fish calls."""

import io
import json
import struct
import wave

import httpx
import pytest

from app import audio, fish_generation
from app.config import settings
from app.fish_audio import FishAudioFailure, normalize_output
from test_fish_audio import sample
from test_fish_generation import fish_case, mocked_http


@pytest.fixture
def mp3(tmp_path):
    source, target = tmp_path / "synthetic.wav", tmp_path / "synthetic.mp3"
    source.write_bytes(sample(rate=44100, channels=2))
    audio.run(
        [
            settings.ffmpeg_binary,
            "-nostdin",
            "-v",
            "error",
            "-y",
            "-i",
            str(source),
            "-c:a",
            "libmp3lame",
            "-b:a",
            "128k",
            str(target),
        ]
    )
    data = target.read_bytes()
    source.unlink()
    target.unlink()
    return data


def test_mp3_real_decode_resample_downmix_and_final_validation(monkeypatch, tmp_path, mp3):
    monkeypatch.setattr(settings, "storage_dir", tmp_path)
    result, receipt = normalize_output(mp3, "mp3")
    assert result[:4] == b"RIFF" and result != mp3
    assert receipt["received_audio"]["container_format"] == "mp3"
    assert receipt["received_audio"]["sample_rate"] == 44100
    assert receipt["received_audio"]["channels"] == 2
    assert receipt["received_audio"]["length_mode"] == "indexed_mp3"
    assert receipt["normalization_applied"]
    with wave.open(io.BytesIO(result), "rb") as wav:
        assert (wav.getframerate(), wav.getnchannels(), wav.getsampwidth()) == (24000, 1, 2)
        assert wav.getnframes() / 24000 == pytest.approx(0.5, abs=0.002)
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("kind", ["mid_frame", "whole_frame", "metadata", "bad_header"])
def test_truncated_mp3_rejected_before_ffmpeg(monkeypatch, mp3, kind):
    if kind == "mid_frame":
        data = mp3[:-20]
    elif kind == "whole_frame":
        # Walk valid MPEG headers to remove exactly the last whole frame;
        # the Xing/Info index must still detect lost audio.
        position = 10 + sum(value << shift for value, shift in zip(mp3[6:10], (21, 14, 7, 0)))
        last = position
        while position < len(mp3):
            last = position
            header = int.from_bytes(mp3[position : position + 4], "big")
            bitrate = (32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320)[
                ((header >> 12) & 15) - 1
            ]
            position += 144000 * bitrate // 44100 + ((header >> 9) & 1)
        data = mp3[:last]
    elif kind == "metadata":
        data = mp3[:8]
    else:
        # Encoder metadata length varies by installed FFmpeg build. Corrupt
        # the actual MPEG header, never an assumed absolute byte offset.
        start = 10 + sum(value << shift for value, shift in zip(mp3[6:10], (21, 14, 7, 0)))
        data = mp3[:start] + b"bad!" + mp3[start + 4 :]
    monkeypatch.setattr(audio, "run", lambda *args: pytest.fail("Invalid framing must not reach FFmpeg"))
    with pytest.raises(FishAudioFailure):
        normalize_output(data, "truncated")


class Chunks(httpx.SyncByteStream):
    def __init__(self, data, error=None):
        self.data, self.error = data, error

    def __iter__(self):
        for pos in range(0, len(self.data), 137):
            yield self.data[pos : pos + 137]
        if self.error:
            raise self.error("private-provider-message secret-token")


def test_http_chunks_assembled_before_wav_finalization(monkeypatch, tmp_path):
    received = sample(rate=44100, channels=2, streaming=True)
    calls = []

    def handler(request):
        calls.append(request)
        assert request.headers["model"] == "s2.1-pro-free"
        assert request.headers["accept-encoding"] == "identity"
        return httpx.Response(
            200,
            stream=Chunks(received),
            headers={"content-type": "audio/wav", "transfer-encoding": "chunked"},
        )

    mocked_http(monkeypatch, tmp_path, handler)
    data, receipt = fish_generation.synthesize(
        tmp_path / "reference", "Test reference.", "Test script.", "chunked"
    )
    assert len(calls) == 1 and data[:4] == b"RIFF"
    facts = receipt["response"]
    assert facts["http_body_complete"] and facts["received_bytes"] == len(received)
    assert facts["transfer_mode"] == "chunked" and facts["api_mode"] == "one_shot_http"
    assert receipt["audio_processing"]["received_audio"]["length_mode"] == "streaming_unknown"
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    "kind,category",
    [
        ("empty", "EMPTY_AUDIO"),
        ("length", "HTTP_LENGTH_MISMATCH"),
        ("json_type", "PROVIDER_NON_AUDIO_RESPONSE"),
        ("json_body", "PROVIDER_ERROR_PAYLOAD"),
        ("html", "PROVIDER_NON_AUDIO_RESPONSE"),
        ("sse", "PROVIDER_NON_AUDIO_RESPONSE"),
        ("truncated_wav", "TRUNCATED_CHUNK"),
        ("disconnect", "TRUNCATED_PROVIDER_RESPONSE"),
        ("timeout", "INCOMPLETE_PROVIDER_RESPONSE"),
        ("conversion", "LOCAL_NORMALIZATION_FAILED"),
    ],
)
def test_http_audio_failures_safe_diagnostics_no_retry(monkeypatch, tmp_path, kind, category):
    data = sample(rate=44100)
    headers = {"content-type": "audio/wav"}
    error = None
    if kind == "empty":
        data = b""
    elif kind == "length":
        headers["content-length"] = str(len(data) + 2)
    elif kind in {"json_type", "json_body", "html", "sse"}:
        data = b'{"error":"private-provider-message secret-token"}'
        headers["content-type"] = {
            "json_type": "application/json",
            "json_body": "audio/wav",
            "html": "text/html",
            "sse": "text/event-stream",
        }[kind]
    elif kind == "truncated_wav":
        data = data[:-2]
    elif kind in {"disconnect", "timeout"}:
        error = httpx.RemoteProtocolError if kind == "disconnect" else httpx.ReadTimeout
    elif kind == "conversion":
        from fastapi import HTTPException

        def fail(*args):
            raise HTTPException(422, "private decoder message")

        monkeypatch.setattr(audio, "run", fail)
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(200, stream=Chunks(data, error), headers=headers)

    mocked_http(monkeypatch, tmp_path, handler)
    with pytest.raises(FishAudioFailure) as caught:
        fish_generation.synthesize(tmp_path / "reference", "Test reference.", "Test script.", "failure")
    diagnostic = caught.value.diagnostic
    assert diagnostic["category"] == category and not diagnostic["audio_accepted"]
    assert diagnostic["response"]["provider_http_status"] == 200
    assert diagnostic["response"]["http_body_complete"] == (
        kind in {"empty", "json_body", "truncated_wav", "conversion"}
    )
    assert len(calls) == 1 and list(tmp_path.iterdir()) == []
    assert "private" not in json.dumps(diagnostic) + caught.value.detail
    assert "secret-token" not in json.dumps(diagnostic)


def test_mp3_http_success_provenance(monkeypatch, tmp_path, mp3):
    mocked_http(
        monkeypatch,
        tmp_path,
        lambda request: httpx.Response(200, content=mp3, headers={"content-type": "audio/mpeg"}),
    )
    data, receipt = fish_generation.synthesize(
        tmp_path / "reference", "Test reference.", "Test script.", "mp3http"
    )
    assert receipt["response"]["content_type"] == "audio/mpeg"
    assert receipt["response"]["content_length_matches"]
    assert receipt["audio_processing"]["received_audio"]["container_format"] == "mp3"
    assert receipt["requested_output"] == {"format": "mp3", "sample_rate": 44100, "mp3_bitrate": 128}
    assert receipt["response"]["consumption"] == "complete_body_before_validation"
    assert receipt["audio_processing"]["source_probe"]["tool"] == "ffprobe"
    assert receipt["audio_processing"]["source_probe"]["codec"] == "mp3"
    assert data[:4] == b"RIFF"


def test_ffmpeg_output_revalidated_and_cleaned(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "storage_dir", tmp_path)

    def fake_conversion(command):
        from pathlib import Path

        malformed = bytearray(sample(rate=24000))
        struct.pack_into("<I", malformed, 40, len(malformed) * 3)
        Path(command[-1]).write_bytes(malformed)

    monkeypatch.setattr(audio, "run", fake_conversion)
    with pytest.raises(FishAudioFailure):
        normalize_output(sample(rate=44100), "badconversion")
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("kind", ["truncated", "json", "disconnect"])
def test_bad_http_never_creates_asset_or_finance(client, artist, studio, monkeypatch, terms, tmp_path, kind):
    _, _, _, body = fish_case(client, artist, studio, monkeypatch, terms)
    before = client.get("/api/assets", headers=studio).json()
    received = sample()[:-20] if kind == "truncated" else b'{"error":"private-message"}'
    error = httpx.RemoteProtocolError if kind == "disconnect" else None
    mocked_http(monkeypatch, tmp_path, lambda request: httpx.Response(200, stream=Chunks(received, error)))
    response = client.post("/api/generations", headers=studio, json=body)
    assert response.status_code == 502, response.text
    saved = client.get("/api/generations", headers=studio).json()[0]
    assert saved["status"] == "FAILED" and saved["asset_id"] is None
    assert not saved["receipt"]["failure"]["audio_accepted"]
    assert client.get("/api/assets", headers=studio).json() == before
    assert client.get("/api/royalties", headers=artist).json() == []
    assert client.get("/api/invoices", headers=artist).json() == []
    monkeypatch.setattr(fish_generation, "synthesize", lambda *args: pytest.fail("No replay"))
    assert client.post("/api/generations", headers=studio, json=body).json()["id"] == saved["id"]


def test_reported_finite_near_uint32_header_remains_rejected(monkeypatch):
    # Match only the saved format/length facts with a synthetic payload. The
    # real response bytes were discarded; this is not its reconstruction.
    data = bytearray(sample(rate=24000, frames=1019750))
    assert len(data) == 2039544
    struct.pack_into("<I", data, 4, 4294967076)
    struct.pack_into("<I", data, 40, 4294967040)
    monkeypatch.setattr(audio, "run", lambda *args: pytest.fail("Finite truncated claims cannot be repaired"))
    with pytest.raises(FishAudioFailure) as caught:
        normalize_output(bytes(data), "reported")
    facts = caught.value.diagnostic["received_audio"]
    assert caught.value.diagnostic["category"] == "TRUNCATED_CHUNK"
    assert facts["failed_chunk"] == "data" and facts["chunk_offset"] == 36
    assert facts["declared_chunk_size"] == 4294967040
    assert facts["available_chunk_bytes"] == 2039500


@pytest.mark.parametrize("padding", [True, False])
def test_odd_sized_wav_metadata_requires_padding(monkeypatch, tmp_path, padding):
    monkeypatch.setattr(settings, "storage_dir", tmp_path)
    original = sample(rate=24000)
    junk = b"JUNK" + struct.pack("<I", 1) + b"x" + (b"\0" if padding else b"")
    data = bytearray(original[:12] + junk + original[12:])
    struct.pack_into("<I", data, 4, len(data) - 8)
    if not padding:
        with pytest.raises(FishAudioFailure):
            normalize_output(bytes(data), "missingpad")
    else:
        normalized, receipt = normalize_output(bytes(data), "padded")
        assert receipt["normalized_audio"]["sample_frames"] == 12000
        with wave.open(io.BytesIO(normalized), "rb") as wav:
            assert wav.readframes(12000) == original[44:]


@pytest.mark.parametrize("failure", ["probe_error", "probe_json", "probe_codec", "probe_rate", "conversion"])
def test_mp3_probe_and_conversion_failures_create_no_asset(
    client, artist, studio, monkeypatch, terms, tmp_path, mp3, failure
):
    import subprocess
    from fastapi import HTTPException

    _, _, _, body = fish_case(client, artist, studio, monkeypatch, terms)
    before = client.get("/api/assets", headers=studio).json()
    original_run = audio.run

    def run(command, *args, **kwargs):
        is_probe = command[0] == settings.ffprobe_binary
        if failure == "conversion" and not is_probe:
            raise HTTPException(422, "private decoder message")
        if is_probe and failure != "conversion":
            if failure == "probe_error":
                raise HTTPException(422, "private probe message")
            document = {
                "format": {"format_name": "mp3", "duration": "0.5"},
                "streams": [
                    {"codec_type": "audio", "codec_name": "mp3", "sample_rate": "44100", "channels": 2}
                ],
            }
            if failure == "probe_codec":
                document["streams"][0]["codec_name"] = "aac"
            elif failure == "probe_rate":
                document["streams"][0]["sample_rate"] = "32000"
            return subprocess.CompletedProcess(
                command,
                0,
                stdout=b"private invalid JSON" if failure == "probe_json" else json.dumps(document).encode(),
            )
        return original_run(command, *args, **kwargs)

    monkeypatch.setattr(audio, "run", run)
    mocked_http(
        monkeypatch,
        tmp_path,
        lambda request: httpx.Response(200, stream=Chunks(mp3), headers={"content-type": "audio/mpeg"}),
    )
    response = client.post("/api/generations", headers=studio, json=body)
    assert response.status_code == 502, response.text
    saved = client.get("/api/generations", headers=studio).json()[0]
    assert saved["status"] == "FAILED" and saved["asset_id"] is None
    expected = (
        "LOCAL_NORMALIZATION_FAILED"
        if failure == "conversion"
        else "MP3_PROBE_FAILED"
        if failure == "probe_error"
        else "MP3_PROBE_INVALID"
    )
    assert saved["receipt"]["failure"]["category"] == expected
    assert saved["receipt"]["failure"]["response"]["http_body_complete"]
    assert client.get("/api/assets", headers=studio).json() == before
    assert client.get("/api/royalties", headers=artist).json() == []
    assert client.get("/api/invoices", headers=artist).json() == []
    assert "private" not in response.text + json.dumps(saved["receipt"])
    assert not list(tmp_path.glob("*-fish-*"))


def test_complete_mp3_http_creates_only_normalized_uploaded_asset(
    client, artist, studio, monkeypatch, terms, tmp_path, mp3
):
    import msgpack

    _, _, _, body = fish_case(client, artist, studio, monkeypatch, terms)
    calls = []

    def handler(request):
        calls.append(request)
        payload = msgpack.unpackb(request.content, raw=False)
        assert str(request.url) == "https://api.fish.audio/v1/tts"
        assert request.headers["model"] == "s2.1-pro-free"
        assert request.headers["accept"] == "audio/mpeg"
        assert (payload["format"], payload["sample_rate"], payload["mp3_bitrate"]) == ("mp3", 44100, 128)
        assert "streaming" not in payload
        return httpx.Response(
            200, stream=Chunks(mp3), headers={"content-type": "audio/mpeg", "transfer-encoding": "chunked"}
        )

    mocked_http(monkeypatch, tmp_path, handler)
    response = client.post("/api/generations", headers=studio, json=body)
    assert response.status_code == 201, response.text
    job = response.json()
    assert job["status"] == "SUCCEEDED" and len(calls) == 1
    assert job["receipt"]["response"]["http_body_complete"]
    assert job["receipt"]["audio_processing"]["source_probe"]["format"] == "mp3"
    assert job["receipt"]["audio_processing"]["normalized_audio"]["sample_rate"] == 24000
    asset = client.get(f"/api/assets/{job['asset_id']}", headers=studio).json()
    assert asset["status"] == "UPLOADED" and asset["authorization_state"] == "unresolved"
    assert asset["analysis"] is None
    content = client.get(f"/api/assets/{job['asset_id']}/audio", headers=studio).content
    with wave.open(io.BytesIO(content), "rb") as wav:
        assert (wav.getframerate(), wav.getnchannels(), wav.getsampwidth()) == (24000, 1, 2)
    assert client.get("/api/royalties", headers=artist).json() == []
    assert client.get("/api/invoices", headers=artist).json() == []
