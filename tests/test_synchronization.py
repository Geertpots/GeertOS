"""Sprint 8B: centrale opslag en bescherming tegen gelijktijdig overschrijven."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

import cloud_database
import database


@pytest.fixture()
def synchronized_sqlite(monkeypatch, tmp_path: Path) -> Path:
    path = tmp_path / "synchronization.db"
    monkeypatch.setattr(cloud_database, "database_url", lambda: "")
    monkeypatch.setattr(cloud_database, "sqlite_path", lambda: path)
    database.init_db()
    return path


def test_change_is_immediately_visible_to_another_device(
    synchronized_sqlite: Path,
) -> None:
    version = database.get_sync_version("expenses")
    changed = pd.DataFrame(
        [
            {
                "category": "Test",
                "description": "Wijziging vanaf iPhone",
                "monthly_amount": 123.45,
            }
        ]
    )

    database.replace_table("expenses", changed, expected_version=version)

    laptop_view = database.read_table("expenses")
    assert laptop_view["description"].tolist() == ["Wijziging vanaf iPhone"]
    assert laptop_view["monthly_amount"].astype(float).tolist() == [123.45]
    assert database.get_sync_version("expenses") == version + 1


def test_stale_device_cannot_overwrite_newer_data(
    synchronized_sqlite: Path,
) -> None:
    laptop_version = database.get_sync_version("family_members")
    iphone_version = laptop_version
    iphone_change = pd.DataFrame(
        [
            {
                "name": "Christel",
                "relationship": "Partner",
                "birth_date": "1970-09-07",
                "notes": "Nieuwste cloudwaarde",
            }
        ]
    )
    stale_laptop_change = iphone_change.assign(notes="Oud laptopscherm")

    database.replace_table(
        "family_members", iphone_change, expected_version=iphone_version
    )

    with pytest.raises(database.SyncConflictError):
        database.replace_table(
            "family_members",
            stale_laptop_change,
            expected_version=laptop_version,
        )

    current = database.read_table("family_members")
    assert current["notes"].tolist() == ["Nieuwste cloudwaarde"]


def test_opa_deposit_updates_shared_version(synchronized_sqlite: Path) -> None:
    version = database.get_sync_version("opa_transactions")

    database.add_opa_transaction("Aydin", "2026-07-28", 25.0, "Test")

    assert database.get_sync_version("opa_transactions") == version + 1
    transactions = database.read_table("opa_transactions")
    assert len(transactions) == 1
    assert float(transactions.iloc[0]["amount"]) == 25.0


def test_missing_sync_state_is_repaired_automatically(
    synchronized_sqlite: Path,
) -> None:
    with database.connection() as db:
        db.execute(
            database.placeholders(
                "DELETE FROM sync_state WHERE table_name = ?"
            ),
            ("plan_actuals",),
        )

    assert database.get_sync_version("plan_actuals") == 0

    with database.connection() as db:
        restored = database.scalar(
            db,
            "SELECT version FROM sync_state WHERE table_name = ?",
            ("plan_actuals",),
        )
    assert int(restored) == 0
