"""Run a loopback-only QA backend with an isolated DB/uploads and no AI credentials."""

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8001)
    args = parser.parse_args()
    workspace = ROOT / ".tmp" / "qa"
    workspace.mkdir(parents=True, exist_ok=True)
    os.environ.update(
        {
            "DATABASE_URL": "sqlite:///" + (workspace / "fairmodel.db").as_posix(),
            "STORAGE_DIR": str(workspace / "uploads"),
            "APP_ENV": "test",
            "DEMO_MODE": "true",
            "PAYMENT_PROVIDER": "mock",
            "ENABLE_SPEAKER_VERIFICATION": "false",
            "GEMINI_API_KEY": "",
            "GROQ_API_KEY": "",
            "PAYPAL_CLIENT_ID": "",
            "PAYPAL_CLIENT_SECRET": "",
            "PAYPAL_WEBHOOK_ID": "",
            "PAYPAL_ALLOW_DRAFTS": "false",
            "PAYPAL_ALLOW_SENDING": "false",
        }
    )
    probes = list((ROOT / "tools" / "ffmpeg-dist").glob("**/ffprobe.exe"))
    if probes:
        os.environ["FFPROBE_BINARY"] = str(probes[0])
        os.environ["FFMPEG_BINARY"] = str(probes[0].with_name("ffmpeg.exe"))
    sys.path.insert(0, str(ROOT / "backend"))
    os.chdir(ROOT / "backend")
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
