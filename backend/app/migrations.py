"""Local versioned migrations; consistent SQLite backups preserve committed WAL data."""

import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from .db import Base

SCHEMA_VERSION = 7


def upgrade_voice_providers(engine):
    """Rebuild only the grant unique key, atomically; keep IDs and child references."""
    with engine.connect() as connection:
        columns = {row[1] for row in connection.exec_driver_sql("PRAGMA table_info(voice_generation_grants)")}
    if "provider" in columns:
        return
    raw = engine.raw_connection()
    try:
        raw.rollback()
        cursor = raw.cursor()
        cursor.execute("PRAGMA foreign_keys=OFF")
        cursor.execute("BEGIN IMMEDIATE")
        cursor.execute("""CREATE TABLE voice_generation_grants_v7 (
            id VARCHAR PRIMARY KEY NOT NULL, created_at VARCHAR NOT NULL, updated_at VARCHAR NOT NULL,
            reference_id VARCHAR NOT NULL REFERENCES reference_voices(id),
            license_id VARCHAR NOT NULL REFERENCES licenses(id), license_version INTEGER NOT NULL,
            artist_id VARCHAR NOT NULL REFERENCES personas(id), studio_id VARCHAR NOT NULL REFERENCES personas(id),
            consent_path VARCHAR NOT NULL, consent_hash VARCHAR NOT NULL, note VARCHAR NOT NULL,
            revoked_at VARCHAR, provider VARCHAR NOT NULL DEFAULT 'gemini', reference_text VARCHAR,
            UNIQUE(reference_id, license_id, license_version, provider))""")
        fields = "id,created_at,updated_at,reference_id,license_id,license_version,artist_id,studio_id,consent_path,consent_hash,note,revoked_at"
        cursor.execute(
            f"INSERT INTO voice_generation_grants_v7 ({fields}) SELECT {fields} FROM voice_generation_grants"
        )
        cursor.execute("DROP TABLE voice_generation_grants")
        cursor.execute("ALTER TABLE voice_generation_grants_v7 RENAME TO voice_generation_grants")
        cursor.execute("ALTER TABLE speech_generations ADD COLUMN provider VARCHAR NOT NULL DEFAULT 'gemini'")
        if cursor.execute("PRAGMA foreign_key_check").fetchall():
            raise RuntimeError("Voice-provider migration failed foreign-key validation; rolled back.")
        raw.commit()
    except Exception:
        raw.rollback()
        raise
    finally:
        raw.cursor().execute("PRAGMA foreign_keys=ON")
        raw.close()


def migrate(engine) -> Path | None:
    with engine.connect() as connection:
        version = connection.exec_driver_sql("PRAGMA user_version").scalar()
    if version not in (0, 1, 2, 3, 4, 5, 6, 7):
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
    # Create missing tables; v7 separately expands grant uniqueness by provider.
    Base.metadata.create_all(engine)
    if version < 7:
        upgrade_voice_providers(engine)
    if version < 5:
        from sqlalchemy import select
        from sqlalchemy.orm import Session
        from .db import Analysis, Report, UsageAuthorization
        from .passports import capture_revision

        with Session(engine) as session:
            for model, kind in (
                (Analysis, "analysis"),
                (Report, "compliance"),
                (UsageAuthorization, "authorization"),
            ):
                for record in session.scalars(select(model)):
                    capture_revision(session, kind, record, origin="migration_current_only")
            session.commit()
    with engine.begin() as connection:
        connection.exec_driver_sql(f"PRAGMA user_version={SCHEMA_VERSION}")
    return backup_path
