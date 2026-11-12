"""Supervise the two app processes in one free, ephemeral Render container.

No provider calls, fixture seeding, credentials output or financial operations.
Backend lifespan owns its existing schema creation/migrations in the new cloud DB.
"""

import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen


def validate_environment(env):
    if not env.get("DEMO_ACCESS_USER") or ":" in env["DEMO_ACCESS_USER"]:
        raise ValueError("Set DEMO_ACCESS_USER to a nonempty username without a colon.")
    if len(env.get("DEMO_ACCESS_PASSWORD", "")) < 24:
        raise ValueError("Set a DEMO_ACCESS_PASSWORD of at least 24 characters in Render.")
    for name in ("PAYPAL_ALLOW_DRAFTS", "PAYPAL_ALLOW_SENDING"):
        if env.get(name, "false").lower() not in ("false", "0", "no", "off", ""):
            raise ValueError("PayPal writes must stay disabled on this ephemeral deployment.")
    # Never accept a public upstream or the developer's original database here.
    if env.get("BACKEND_URL") != "http://127.0.0.1:8000":
        raise ValueError("The hosted backend must remain loopback-only.")
    if env.get("DATABASE_URL") != "sqlite:////tmp/fairmodel/fairmodel.db":
        raise ValueError("This free demo uses only its isolated temporary database.")
    if env.get("STORAGE_DIR") != "/tmp/fairmodel/storage":
        raise ValueError("This free demo uses only its isolated temporary uploads.")
    port = int(env.get("PORT", "10000"))
    if not 1024 <= port <= 65535 or port == 8000:
        raise ValueError("Choose a valid public PORT different from the private API port.")
    return port


def stop_children(children):
    for child in children:
        if child.poll() is None:
            child.terminate()
    for child in children:
        try:
            child.wait(timeout=10)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait()


def main():
    env = os.environ.copy()
    port = validate_environment(env)
    root = Path(__file__).resolve().parents[1]
    Path(env["STORAGE_DIR"]).mkdir(parents=True, exist_ok=True)
    env.update(HOSTED_DEMO="true", HOSTNAME="0.0.0.0", PORT=str(port))
    children = []
    stopping = False

    def shutdown(_signum, _frame):
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)
    try:
        children.append(subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1",
             "--port", "8000", "--workers", "1", "--no-access-log"],
            cwd=root / "backend", env=env,
        ))
        deadline = time.monotonic() + 90
        while not stopping and children[0].poll() is None and time.monotonic() < deadline:
            try:
                with urlopen("http://127.0.0.1:8000/health", timeout=2) as response:
                    if response.status == 200:
                        break
            except (URLError, TimeoutError):
                time.sleep(0.25)
        else:
            if stopping:
                return 0
            raise RuntimeError("Private API did not become ready; frontend was not started.")
        children.append(subprocess.Popen(
            ["node", "server.js"], cwd=root / "frontend", env=env,
        ))
        print("Temporary hosted demo readying; storage is ephemeral; PayPal writes disabled.", flush=True)
        while not stopping:
            if any(child.poll() is not None for child in children):
                raise RuntimeError("An application process exited; stopping the other process.")
            time.sleep(0.25)
        return 0
    finally:
        stop_children(children)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, RuntimeError) as error:
        print(f"Deployment startup failed: {error}", file=sys.stderr)
        sys.exit(1)
