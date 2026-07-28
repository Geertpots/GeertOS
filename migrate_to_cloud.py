"""Veilige eenmalige migratie van Sprint 7 SQLite naar PostgreSQL.

Gebruik uitsluitend met GEERTOS_DATABASE_URL ingesteld op de doelomgeving.
De bestaande SQLite-database wordt nooit gewijzigd.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path


TABLES = [
    "settings",
    "balance_items",
    "etf_positions",
    "bitcoin_transactions",
    "expenses",
    "family_members",
    "opa_funds",
    "opa_transactions",
]

CONTROL_COLUMNS = {
    "balance_items": ["amount"],
    "etf_positions": ["invested", "value"],
    "bitcoin_transactions": ["amount_eur", "btc_amount"],
    "expenses": ["monthly_amount"],
    "opa_funds": ["target_amount", "expected_return_pct"],
    "opa_transactions": ["amount"],
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sqlite_snapshot(source: Path) -> dict[str, object]:
    with sqlite3.connect(source) as db:
        integrity = db.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise RuntimeError(f"SQLite-integriteitscontrole mislukt: {integrity}")
        snapshot: dict[str, object] = {"tables": {}}
        for table in TABLES:
            columns = CONTROL_COLUMNS.get(table, [])
            sums = {
                column: float(
                    db.execute(
                        f"SELECT COALESCE(SUM({column}), 0) FROM {table}"
                    ).fetchone()[0]
                )
                for column in columns
            }
            snapshot["tables"][table] = {
                "count": db.execute(
                    f"SELECT COUNT(*) FROM {table}"
                ).fetchone()[0],
                "sums": sums,
            }
        return snapshot


def make_source_backup(source: Path, destination: Path) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = destination / f"sprint7_voor_cloud_{stamp}.db"
    shutil.copy2(source, target)
    metadata = {
        "created_at": datetime.now().isoformat(),
        "source": str(source.resolve()),
        "backup": str(target.resolve()),
        "sha256": sha256(target),
        "snapshot": sqlite_snapshot(target),
    }
    target.with_suffix(".json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    return target


def source_rows(source: Path, table: str) -> list[dict[str, object]]:
    with sqlite3.connect(source) as db:
        db.row_factory = sqlite3.Row
        return [dict(row) for row in db.execute(f"SELECT * FROM {table}")]


def migrate(source: Path) -> dict[str, object]:
    from config import database_url

    if not database_url():
        raise RuntimeError(
            "Stel GEERTOS_DATABASE_URL eerst veilig in via de omgeving "
            "of .streamlit/secrets.toml."
        )

    # Pas na bovenstaande veiligheidscontrole wordt de doelconfiguratie geladen.
    from cloud_database import connection, placeholders, rows_as_dicts
    from database import init_db

    expected = sqlite_snapshot(source)
    init_db()
    with connection() as target:
        for table in reversed(TABLES):
            target.execute(f"DELETE FROM {table}")

        for table in TABLES:
            rows = source_rows(source, table)
            if not rows:
                continue
            columns = list(rows[0])
            marks = ",".join("?" for _ in columns)
            target.executemany(
                placeholders(
                    f"INSERT INTO {table} ({','.join(columns)}) VALUES ({marks})"
                ),
                [tuple(row[column] for column in columns) for row in rows],
            )

        for table in TABLES:
            if table == "settings":
                continue
            target.execute(
                f"""
                SELECT setval(
                    pg_get_serial_sequence('{table}', 'id'),
                    COALESCE((SELECT MAX(id) FROM {table}), 1),
                    (SELECT COUNT(*) > 0 FROM {table})
                )
                """
            )

    actual: dict[str, object] = {"tables": {}}
    with connection() as target:
        for table in TABLES:
            rows = rows_as_dicts(target.execute(f"SELECT * FROM {table}"))
            sums = {
                column: float(sum((row[column] or 0) for row in rows))
                for column in CONTROL_COLUMNS.get(table, [])
            }
            actual["tables"][table] = {"count": len(rows), "sums": sums}

    if actual != expected:
        raise RuntimeError(
            "Migratiecontrole mislukt. De bronback-up blijft intact; "
            f"verwacht={expected!r}, werkelijk={actual!r}"
        )
    return actual


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source",
        type=Path,
        default=Path(__file__).with_name("project_vrijheid.db"),
    )
    parser.add_argument(
        "--backup-dir",
        type=Path,
        default=Path(__file__).with_name("backups"),
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Zonder deze vlag wordt alleen back-up en controle uitgevoerd.",
    )
    args = parser.parse_args()
    source = args.source.resolve()
    backup = make_source_backup(source, args.backup_dir)
    print(f"Back-up gecontroleerd: {backup}")
    if not args.execute:
        print("Proefcontrole voltooid; PostgreSQL is niet gewijzigd.")
        return
    result = migrate(source)
    print(json.dumps(result, indent=2))
    print("Migratie en controle zijn geslaagd.")


if __name__ == "__main__":
    main()
