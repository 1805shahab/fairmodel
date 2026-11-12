"""Exercise the real runtime dependency, not the financial fixture override."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.responses import StreamingResponse
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import Session

from app import db as database
from app.db import Base, Persona


def setup_engine(tmp_path, monkeypatch):
    engine = create_engine(
        "sqlite:///" + (tmp_path / "reads.db").as_posix(),
        connect_args={"check_same_thread": False, "timeout": 2},
    )
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add(Persona(id="first", role="artist", name="Fixture", email="fixture@example.test"))
        db.commit()
    monkeypatch.setattr(database, "engine", engine)
    return engine


def test_concurrent_record_reads_do_not_take_a_writer_lock(tmp_path, monkeypatch):
    engine = setup_engine(tmp_path, monkeypatch)
    probe = FastAPI()
    barrier = Barrier(2)

    @probe.get("/read")
    def read(db: Annotated[Session, Depends(database.get_session, scope="function")]):
        count = db.scalar(select(func.count()).select_from(Persona))
        barrier.wait(timeout=3)
        return {"count": count}

    try:
        with TestClient(probe) as client, ThreadPoolExecutor(max_workers=2) as pool:
            responses = list(pool.map(lambda _: client.get("/read"), range(2)))
            assert all(
                response.status_code == 200 and response.json()["count"] == 1 for response in responses
            )
    finally:
        engine.dispose()


def test_session_releases_before_private_response_streams(tmp_path, monkeypatch):
    engine = setup_engine(tmp_path, monkeypatch)
    probe = FastAPI()

    @probe.get("/stream")
    def stream(db: Annotated[Session, Depends(database.get_session, scope="function")]):
        assert db.get(Persona, "first")

        def content():
            # A separate writer must succeed while the response body is streaming.
            with Session(engine) as writer:
                writer.add(
                    Persona(
                        id="during-stream", role="studio", name="Fixture studio", email="studio@example.test"
                    )
                )
                writer.commit()
            yield b"writer committed"

        return StreamingResponse(content(), media_type="text/plain")

    try:
        with TestClient(probe) as client:
            response = client.get("/stream")
            assert response.status_code == 200 and response.content == b"writer committed"
    finally:
        engine.dispose()
