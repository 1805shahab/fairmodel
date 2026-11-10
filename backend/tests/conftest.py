import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

PROJECT = Path(__file__).resolve().parents[2]
TEST_RUNS = PROJECT / ".tmp" / "pytest"
TEST_RUNS.mkdir(parents=True, exist_ok=True)
# A fresh owned directory avoids inaccessible shared Windows pytest directories
# and keeps concurrent runs separate from one another and from application data.
TEST_ROOT = tempfile.TemporaryDirectory(prefix="run-", dir=TEST_RUNS)
os.environ["DATABASE_URL"] = "sqlite:///" + (Path(TEST_ROOT.name) / "lifespan.db").as_posix()
os.environ["STORAGE_DIR"] = str(Path(TEST_ROOT.name) / "uploads")
os.environ["GEMINI_API_KEY"] = ""
os.environ["GROQ_API_KEY"] = ""
os.environ["PAYPAL_CLIENT_ID"] = ""
os.environ["PAYPAL_CLIENT_SECRET"] = ""
os.environ["PAYPAL_WEBHOOK_ID"] = ""
os.environ["PAYPAL_ALLOW_DRAFTS"] = "false"
os.environ["PAYPAL_ALLOW_SENDING"] = "false"
os.environ["PAYMENT_PROVIDER"] = "mock"
os.environ["DEMO_MODE"] = "true"

from app.config import settings  # noqa: E402
from app.db import Base, engine, get_session  # noqa: E402
from app.main import app  # noqa: E402

ffprobes = list((PROJECT / "tools" / "ffmpeg-dist").glob("**/ffprobe.exe"))
if ffprobes:
    settings.ffprobe_binary = str(ffprobes[0])
    settings.ffmpeg_binary = str(ffprobes[0].with_name("ffmpeg.exe"))


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    # Run before pytest builds its temporary-path factory. Never pass a shared
    # runtime directory: pytest clears an explicit basetemp before using it.
    if config.option.basetemp is None:
        config.option.basetemp = str(Path(TEST_ROOT.name) / "cases")


def pytest_sessionfinish(session, exitstatus):
    # Release SQLite handles before TemporaryDirectory cleanup on Windows.
    engine.dispose()


@pytest.fixture(autouse=True)
def backend_working_directory(monkeypatch):
    # Match the supported runtime layout even when pytest starts at repo root.
    # Restore afterward; do not change cwd during collection of CLI test paths.
    monkeypatch.chdir(PROJECT / "backend")


@pytest.fixture
def client(tmp_path):
    test_engine = create_engine(
        "sqlite:///" + (tmp_path / "case.db").as_posix(),
        connect_args={"check_same_thread": False, "timeout": 10},
    )

    @event.listens_for(test_engine, "connect")
    def foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(test_engine)
    from app.main import seed

    with Session(test_engine) as session:
        seed(session)
        session.commit()

    def override():
        with Session(test_engine, expire_on_commit=False) as session:
            session.connection().exec_driver_sql("BEGIN IMMEDIATE")
            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise

    app.dependency_overrides[get_session] = override
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    test_engine.dispose()


@pytest.fixture
def artist():
    return {"X-Demo-Persona": "artist_demo"}


@pytest.fixture
def studio():
    return {"X-Demo-Persona": "studio_demo"}


@pytest.fixture
def terms():
    from app.schemas import Terms

    return Terms(
        artist="Amara",
        studio="Northstar",
        start_date="2026-01-01",
        end_date="2027-12-31",
        permitted_media=["online advertising"],
        territories=["US"],
        languages=["English"],
        campaigns=["*"],
        included_seconds="30",
        billing_basis="per_asset",
        additional_rate="2.00",
        currency="USD",
        additional_usage_permitted=True,
        restricted_categories=["political advertising"],
    )
