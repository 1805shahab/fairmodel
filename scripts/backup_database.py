"""Consistent local SQLite backup; prints location/integrity, never database contents."""

import json
import sqlite3
import sys
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

if __name__ == "__main__":
    from app.db import engine

    source = Path(engine.url.database).resolve()
    if not source.is_file():
        raise SystemExit("Existing database not found; no database was created.")
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    target = source.parent / "backups" / f"fairmodel-before-paypal-{stamp}.db"
    target.parent.mkdir(exist_ok=True)
    with (
        closing(sqlite3.connect(source)) as before,
        closing(sqlite3.connect(target)) as backup,
    ):
        before.backup(backup)
        print(
            json.dumps(
                {
                    "backup": str(target),
                    "schema": backup.execute("PRAGMA user_version").fetchone()[0],
                    "integrity": backup.execute("PRAGMA quick_check").fetchone()[0],
                }
            )
        )
