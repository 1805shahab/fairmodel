"""Additive local migrations. Backups include committed WAL data via SQLite's backup API."""

import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from .db import Base

SCHEMA_VERSION = 4


def migrate(engine) -> Path | None:
    with engine.connect() as connection:
        version = connection.exec_driver_sql("PRAGMA user_version").scalar()
    if version not in (0, 1, 2, 3, 4):
        raise RuntimeError("Unsupported database schema version. Back up before migration.")
    backup_path = None
    database = engine.url.database
    if version < SCHEMA_VERSION and database and database != ":memory:" and Path(database).is_file():
        source_path = Path(database).resolve()
        backup_dir = source_path.parent / "backups"
        backup_dir.mkdir(exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        backup_path = backup_dir / f"{source_path.stem}-pre-v{SCHEMA_VERSION}-{stamp}.db"
        with (
            closing(sqlite3.connect(str(source_path))) as source,
            closing(sqlite3.connect(str(backup_path))) as destination,
        ):
            source.backup(destination)
    # v3 -> v4 adds payment metadata/operation/receipt tables. No ALTER/DROP/data rewrite.
    Base.metadata.create_all(engine)
    with engine.begin() as connection:
        connection.exec_driver_sql(f"PRAGMA user_version={SCHEMA_VERSION}")
    return backup_path
