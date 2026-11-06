import importlib.util
import wave
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "optional_verify", Path(__file__).parents[1] / "optional-speaker" / "verify.py"
)
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)


def test_worker_import_requires_no_heavy_dependencies():
    assert worker.MODEL == "speechbrain/spkrec-ecapa-voxceleb"


def test_worker_rejects_short_and_silent_audio_before_model_loading(tmp_path):
    path = tmp_path / "silent.wav"
    with wave.open(str(path), "wb") as sample:
        sample.setnchannels(1)
        sample.setsampwidth(2)
        sample.setframerate(16000)
        sample.writeframes(b"\0\0" * 16000 * 3)
    with pytest.raises(ValueError, match="Insufficient audible signal"):
        worker.read_pcm(path)


def test_worker_rejects_nonfinite_threshold():
    with pytest.raises(ValueError, match="threshold"):
        worker.verify(Path("unused"), Path("unused"), float("nan"), False, Path("unused"), "main")
