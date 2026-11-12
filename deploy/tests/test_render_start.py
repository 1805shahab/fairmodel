"""Deployment checks only; never load application settings or real .env files."""

import importlib.util
import subprocess
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "render_start", Path(__file__).resolve().parents[1] / "render_start.py"
)
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)


def valid_env():
    return {
        "DEMO_ACCESS_USER": "test-owner",
        "DEMO_ACCESS_PASSWORD": "synthetic-test-password-no-secret",
        "BACKEND_URL": "http://127.0.0.1:8000",
        "DATABASE_URL": "sqlite:////tmp/fairmodel/fairmodel.db",
        "STORAGE_DIR": "/tmp/fairmodel/storage",
    }


def test_free_runtime_uses_single_private_backend():
    assert launcher.validate_environment(valid_env()) == 10000


@pytest.mark.parametrize("key,value", [
    ("DEMO_ACCESS_USER", ""), ("DEMO_ACCESS_USER", "wrong:user"),
    ("DEMO_ACCESS_PASSWORD", "short"), ("PAYPAL_ALLOW_DRAFTS", "true"),
    ("PAYPAL_ALLOW_SENDING", "true"), ("PAYPAL_ALLOW_DRAFTS", "1"),
    ("BACKEND_URL", "https://external.example"),
    ("DATABASE_URL", "sqlite:///./fairmodel.db"),
    ("STORAGE_DIR", "storage"), ("PORT", "8000"), ("PORT", "0"),
])
def test_unsafe_startup_is_rejected(key, value):
    env = valid_env()
    env[key] = value
    with pytest.raises(ValueError):
        launcher.validate_environment(env)


def test_render_injected_port():
    env = valid_env()
    env["PORT"] = "10001"
    assert launcher.validate_environment(env) == 10001


def test_supervisor_stops_all_children_and_reaps_hung_process():
    class Child:
        def __init__(self, hangs=False):
            self.hangs = hangs
            self.terminated = self.killed = self.reaped = False

        def poll(self):
            return None

        def terminate(self):
            self.terminated = True

        def wait(self, timeout=None):
            if self.hangs and timeout:
                raise subprocess.TimeoutExpired("synthetic-process", timeout)
            self.reaped = True

        def kill(self):
            self.killed = True

    children = [Child(), Child(hangs=True)]
    launcher.stop_children(children)
    assert all(child.terminated and child.reaped for child in children)
    assert children[1].killed
