"""Regressietests voor de provider-neutrale Sprint 8A-datalaag."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import cloud_database
from migrate_to_cloud import make_source_backup, sqlite_snapshot


def test_sqlite_remains_the_default(monkeypatch) -> None:
    monkeypatch.delenv("GEERTOS_DATABASE_URL", raising=False)
    monkeypatch.setattr(cloud_database, "database_url", lambda: "")
    assert cloud_database.backend_name() == "sqlite"
    assert cloud_database.placeholders("VALUES (?, ?)") == "VALUES (?, ?)"


def test_postgresql_uses_standard_driver_parameters(monkeypatch) -> None:
    monkeypatch.setenv(
        "GEERTOS_DATABASE_URL",
        "postgresql://example.invalid/postgres?sslmode=require",
    )
    assert cloud_database.backend_name() == "postgresql"
    assert cloud_database.placeholders("VALUES (?, ?)") == "VALUES (%s, %s)"


def test_migration_backup_is_complete_and_unchanged(tmp_path: Path) -> None:
    source = tmp_path / "source.db"
    with sqlite3.connect(source) as db:
        for table in (
            "settings",
            "balance_items",
            "etf_positions",
            "bitcoin_transactions",
            "expenses",
            "family_members",
            "opa_funds",
            "opa_transactions",
        ):
            if table == "settings":
                db.execute("CREATE TABLE settings(key TEXT, value TEXT)")
            else:
                columns = {
                    "balance_items": "amount REAL",
                    "etf_positions": "invested REAL, value REAL",
                    "bitcoin_transactions": "amount_eur REAL, btc_amount REAL",
                    "expenses": "monthly_amount REAL",
                    "family_members": "name TEXT",
                    "opa_funds": "target_amount REAL, expected_return_pct REAL",
                    "opa_transactions": "amount REAL",
                }[table]
                db.execute(f"CREATE TABLE {table}({columns})")

    before = source.read_bytes()
    backup = make_source_backup(source, tmp_path / "backups")

    assert source.read_bytes() == before
    assert backup.read_bytes() == before
    metadata = json.loads(backup.with_suffix(".json").read_text(encoding="utf-8"))
    assert metadata["snapshot"] == sqlite_snapshot(source)
