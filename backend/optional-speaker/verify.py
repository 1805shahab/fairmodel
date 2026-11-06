"""Isolated experimental ECAPA-TDNN CLI. Not connected to payment or automatic decisions.

Accepts already-normalized, consented, single-speaker 16kHz mono PCM16 WAVs.
By default model fetching is offline. A first download needs --allow-model-download.
Outputs a score only after successful inference. No score is produced on failure.
"""

import argparse
import array
import json
import math
import sys
import wave
from pathlib import Path

MODEL = "speechbrain/spkrec-ecapa-voxceleb"


def read_pcm(path: Path) -> array.array:
    with wave.open(str(path), "rb") as file:
        if (file.getnchannels(), file.getsampwidth(), file.getframerate()) != (1, 2, 16000):
            raise ValueError("Expected normalized 16kHz mono PCM16 WAV.")
        duration = file.getnframes() / 16000
        if not 3 <= duration <= 120:
            raise ValueError(
                "Experimental input must contain 3–120 seconds of consented single-speaker audio."
            )
        signal = array.array("h", file.readframes(file.getnframes()))
        if not signal or max(abs(x) for x in signal) < 32:
            raise ValueError("Insufficient audible signal.")
        if sys.byteorder != "little":
            signal.byteswap()
        return signal


def verify(
    reference: Path, submitted: Path, threshold: float, allow_download: bool, cache: Path, revision: str
) -> dict:
    if not -1 <= threshold <= 1 or not math.isfinite(threshold):
        raise ValueError("Cosine threshold must be finite and between -1 and 1.")
    ref = read_pcm(reference)
    asset = read_pcm(submitted)
    # Heavy dependencies are deliberately imported only within this standalone worker.
    import torch
    from speechbrain.inference.classifiers import EncoderClassifier
    from speechbrain.utils.fetching import FetchConfig, LocalStrategy

    torch.set_num_threads(1)
    classifier = EncoderClassifier.from_hparams(
        source=MODEL,
        savedir=str(cache),
        run_opts={"device": "cpu"},
        local_strategy=LocalStrategy.COPY,
        fetch_config=FetchConfig(allow_network=allow_download, revision=revision),
    )
    with torch.inference_mode():
        ref_tensor = torch.tensor(ref, dtype=torch.float32).unsqueeze(0) / 32768
        asset_tensor = torch.tensor(asset, dtype=torch.float32).unsqueeze(0) / 32768
        first = classifier.encode_batch(ref_tensor).flatten()
        second = classifier.encode_batch(asset_tensor).flatten()
        score = float(torch.nn.functional.cosine_similarity(first, second, dim=0).item())
    if not math.isfinite(score):
        raise ValueError("Model returned a nonfinite score.")
    return {
        "status": "experimental_match" if score >= threshold else "needs_review",
        "similarity": score,
        "threshold": threshold,
        "threshold_calibrated": False,
        "model": MODEL,
        "revision": revision,
        "device": "cpu",
        "sample_rate": 16000,
        "note": "Uncalibrated experiment. Not proof of cloning, permission, or infringement. Never a charge trigger.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path)
    parser.add_argument("submitted", type=Path)
    parser.add_argument("--threshold", type=float, default=0.7)
    parser.add_argument("--cache", type=Path, default=Path("storage/speaker-model"))
    parser.add_argument("--revision", default="main")
    parser.add_argument("--allow-model-download", action="store_true")
    args = parser.parse_args()
    try:
        result = verify(
            args.reference,
            args.submitted,
            args.threshold,
            args.allow_model_download,
            args.cache,
            args.revision,
        )
    except Exception:
        print(
            json.dumps(
                {
                    "status": "unavailable",
                    "model": MODEL,
                    "note": "Worker did not complete. Check optional dependencies, consented inputs and model cache.",
                }
            )
        )
        return 1
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
