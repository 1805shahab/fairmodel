"""Manually authorized existing-draft issuer repair. Dry-run by default; no PayPal writes."""

import argparse
import json
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))


def main():
    from app.config import settings
    from app.db import engine
    from app.paypal_client import PayPalError
    from app.paypal_provider import PayPalSandboxProvider
    from app.paypal_reconciliation import reconcile_issuer
    from fastapi import HTTPException
    from sqlalchemy.orm import Session

    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("operation-id", "remote-id", "amount", "recipient", "merchant", "note"):
        parser.add_argument("--" + key, required=True)
    parser.add_argument("--actor-id", default="artist_demo")
    parser.add_argument("--currency", default="USD")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--confirm-issuer-correction", action="store_true")
    args = parser.parse_args()
    if args.execute and not args.confirm_issuer_correction:
        parser.error(
            "Execution requires explicit authorization for this issuer correction."
        )
    values = vars(args).copy()
    values.pop("confirm_issuer_correction")
    provider = PayPalSandboxProvider()
    try:
        if args.execute:
            database = Path(settings.database_url.removeprefix("sqlite:///")).resolve()
            backup_dir = Path("backups").resolve()
            backup_dir.mkdir(exist_ok=True)
            backup = backup_dir / (
                "fairmodel-before-issuer-reconcile-"
                + datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
                + ".db"
            )
            with (
                sqlite3.connect(database.as_uri() + "?mode=ro", uri=True) as source,
                sqlite3.connect(backup) as target,
            ):
                source.backup(target)
                if target.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                    raise ValueError("Backup integrity failed")
            print(json.dumps({"consistent_backup": str(backup)}))
        with Session(engine, expire_on_commit=False) as db:
            db.connection().exec_driver_sql(
                "BEGIN IMMEDIATE" if args.execute else "BEGIN"
            )
            try:
                result = reconcile_issuer(db, provider, **values)
                if args.execute:
                    db.commit()
                else:
                    db.rollback()
                print(json.dumps(result))
            except Exception:
                db.rollback()
                raise
    except PayPalError as error:
        print(json.dumps({"status": "HELD", "category": error.category}))
        return 1
    except HTTPException as error:
        print(json.dumps({"status": "HELD", "detail": error.detail}))
        return 1
    finally:
        provider.client.http.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
