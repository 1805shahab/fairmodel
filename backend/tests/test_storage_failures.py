import errno
import sqlite3

import pytest
from sqlalchemy.exc import OperationalError

from app import audio, main
from app.config import settings
from test_workflow import mock_audio, setup_license, submit


def test_full_upload_storage_is_actionable_and_removes_partial_file(
    client, artist, studio, monkeypatch, terms
):
    license_ = setup_license(client, artist, monkeypatch, terms)
    before = set(settings.storage_dir.iterdir())

    def full(_path):
        raise OSError(errno.ENOSPC, "private filesystem detail")

    monkeypatch.setattr(audio, "probe", full)
    response = submit(client, studio, license_["id"])
    assert response.status_code == 507
    assert "Free disk space" in response.json()["detail"]
    assert "private filesystem" not in response.text
    assert set(settings.storage_dir.iterdir()) == before
    assert client.get("/api/assets", headers=studio).json() == []
    assert client.get("/api/royalties", headers=artist).json() == []


@pytest.mark.parametrize("code,status", [(sqlite3.SQLITE_FULL, 507), (sqlite3.SQLITE_BUSY, 503)])
def test_database_failure_rolls_back_upload_and_sanitizes_error(
    client, artist, studio, monkeypatch, terms, code, status
):
    license_ = setup_license(client, artist, monkeypatch, terms)
    mock_audio(monkeypatch)
    original_audit = main.audit
    original_error = sqlite3.OperationalError("private query and database path")
    original_error.sqlite_errorcode = code

    def failed_audit(*_args, **_kwargs):
        raise OperationalError("private statement", {}, original_error)

    monkeypatch.setattr(main, "audit", failed_audit)
    response = submit(client, studio, license_["id"])
    assert response.status_code == status
    assert "private" not in response.text
    assert client.get("/api/assets", headers=studio).json() == []
    assert client.get("/api/royalties", headers=artist).json() == []
    monkeypatch.setattr(main, "audit", original_audit)
    retry = submit(client, studio, license_["id"])
    assert retry.status_code == 201 and not retry.json().get("duplicate")
