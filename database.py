"""Provider-neutrale opslaglaag voor GeertOS (SQLite en PostgreSQL)."""

from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path

import pandas as pd

from cloud_database import (
    backend_name,
    connection,
    placeholders,
    rows_as_dicts,
    scalar,
)
from config import sqlite_path


DB_PATH = sqlite_path()

SYNC_TABLES = (
    "balance_items",
    "etf_positions",
    "bitcoin_transactions",
    "expenses",
    "family_members",
    "opa_funds",
    "opa_transactions",
)


class SyncConflictError(RuntimeError):
    """Een ander apparaat heeft dezelfde gegevens inmiddels gewijzigd."""


def init_db() -> None:
    with connection() as db:
        id_column = (
            "BIGSERIAL PRIMARY KEY"
            if backend_name() == "postgresql"
            else "INTEGER PRIMARY KEY AUTOINCREMENT"
        )
        statements = [
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """,
            f"""
            CREATE TABLE IF NOT EXISTS balance_items (
                id {id_column},
                category TEXT NOT NULL,
                name TEXT NOT NULL,
                amount NUMERIC NOT NULL DEFAULT 0,
                item_type TEXT NOT NULL CHECK(item_type IN ('asset','liability'))
            )
            """,
            f"""
            CREATE TABLE IF NOT EXISTS etf_positions (
                id {id_column},
                name TEXT NOT NULL,
                ticker TEXT NOT NULL,
                invested NUMERIC NOT NULL DEFAULT 0,
                value NUMERIC NOT NULL DEFAULT 0
            )
            """,
            f"""
            CREATE TABLE IF NOT EXISTS bitcoin_transactions (
                id {id_column},
                trade_date TEXT NOT NULL,
                amount_eur NUMERIC NOT NULL,
                btc_amount NUMERIC NOT NULL,
                note TEXT DEFAULT ''
            )
            """,
            f"""
            CREATE TABLE IF NOT EXISTS expenses (
                id {id_column},
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                monthly_amount NUMERIC NOT NULL DEFAULT 0
            )
            """,
            f"""
            CREATE TABLE IF NOT EXISTS family_members (
                id {id_column},
                name TEXT NOT NULL UNIQUE,
                relationship TEXT NOT NULL,
                birth_date TEXT DEFAULT '',
                notes TEXT DEFAULT ''
            )
            """,
            f"""
            CREATE TABLE IF NOT EXISTS opa_funds (
                id {id_column},
                child_name TEXT NOT NULL UNIQUE,
                birth_date TEXT NOT NULL,
                target_amount NUMERIC NOT NULL DEFAULT 25000,
                expected_return_pct NUMERIC NOT NULL DEFAULT 5.0
            )
            """,
            f"""
            CREATE TABLE IF NOT EXISTS opa_transactions (
                id {id_column},
                child_name TEXT NOT NULL,
                transaction_date TEXT NOT NULL,
                amount NUMERIC NOT NULL,
                note TEXT DEFAULT ''
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS sync_state (
                table_name TEXT PRIMARY KEY,
                version BIGINT NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL
            )
            """,
        ]
        for statement in statements:
            db.execute(statement)
        now = datetime.now(UTC).isoformat()
        db.executemany(
            placeholders(
                """
                INSERT INTO sync_state(table_name, version, updated_at)
                VALUES (?, 0, ?)
                ON CONFLICT(table_name) DO NOTHING
                """
            ),
            [(table, now) for table in SYNC_TABLES],
        )
        defaults = {
            "birth_date": "1964-12-21",
            "target_monthly": "4000",
            "calculation_end_year": "2047",
            "inflation_pct": "2.5",
            "etf_return_pct": "4.0",
            "etf_start": "500000",
            "safety_buffer": "100000",
            "annuity_principal": "250000",
            "annuity_years": "15",
            "annuity_return_pct": "2.5",
            "annuity_tax_pct": "37.0",
            "own_pension_monthly": "145",
            "partner_pension_monthly": "350",
            "aow_combined_monthly": "2000",
            "side_income_monthly": "1500",
            "bitcoin_current_price": "60000",
            "dark_mode": "1",
            "sale_property_price": "1595000",
            "sale_property_book": "885000",
            "sale_inventory_price": "275000",
            "sale_inventory_book": "335000",
            "sale_mortgage": "675000",
            "sale_business_credit": "100000",
            "sale_other_loans": "125000",
            "sale_brokerage_pct": "1.75",
            "sale_brokerage_vat_pct": "21",
            "sale_other_costs": "0",
            "sale_tax_pct": "25.8",
            "sale_annuity_reserve": "250000",
            "sale_net_cash_goal": "600000",
        }
        db.executemany(
            placeholders(
                """
                INSERT INTO settings(key, value) VALUES (?, ?)
                ON CONFLICT(key) DO NOTHING
                """
            ),
            defaults.items(),
        )

        if scalar(db, "SELECT COUNT(*) FROM balance_items") == 0:
            db.executemany(
                placeholders("""
                INSERT INTO balance_items(category,name,amount,item_type)
                VALUES (?,?,?,?)
                """),
                [
                    ("Beleggingen", "ETF-portefeuille", 500000, "asset"),
                    ("Buffer", "Spaargeld", 100000, "asset"),
                    ("Lijfrente", "Stakingslijfrente", 250000, "asset"),
                    ("Overig", "Bitcoin", 0, "asset"),
                ],
            )
        if scalar(db, "SELECT COUNT(*) FROM etf_positions") == 0:
            db.executemany(
                placeholders("""
                INSERT INTO etf_positions(name,ticker,invested,value)
                VALUES (?,?,?,?)
                """),
                [
                    ("Wereldwijde aandelen", "VWCE", 350000, 350000),
                    ("Wereldwijde obligaties", "VAGF", 100000, 100000),
                    ("Geldmarkt / kortlopend", "XEON", 50000, 50000),
                ],
            )
        if scalar(db, "SELECT COUNT(*) FROM expenses") == 0:
            db.executemany(
                placeholders("""
                INSERT INTO expenses(category,description,monthly_amount)
                VALUES (?,?,?)
                """),
                [
                    ("Wonen", "Woonlasten", 1200),
                    ("Levensonderhoud", "Boodschappen en dagelijks", 900),
                    ("Vrijheid", "Vakantie en genieten", 750),
                    ("Vervoer", "Auto en vervoer", 550),
                    ("Overig", "Verzekeringen en reservering", 600),
                ],
            )

        if scalar(db, "SELECT COUNT(*) FROM family_members") == 0:
            db.executemany(
                placeholders("""
                INSERT INTO family_members(name,relationship,birth_date,notes)
                VALUES (?,?,?,?)
                """),
                [
                    ("Christel", "Partner", "1970-09-07", ""),
                    ("Brian", "Kind", "", ""),
                    ("Lisa", "Kind", "", ""),
                    ("Laura", "Kind", "", ""),
                    ("Liza", "Bonusdochter", "", ""),
                    ("Roza", "Bonusdochter", "", ""),
                    ("Aydin", "Kleinkind", "2022-04-01", "Geboortedag in april; exacte dag kan worden aangepast."),
                    ("Sade", "Kleinkind", "2024-04-04", ""),
                    ("Isabel", "Kleinkind", "2025-08-01", ""),
                ],
            )
        if scalar(db, "SELECT COUNT(*) FROM opa_funds") == 0:
            db.executemany(
                placeholders("""
                INSERT INTO opa_funds(child_name,birth_date,target_amount,expected_return_pct)
                VALUES (?,?,?,?)
                """),
                [
                    ("Aydin", "2022-04-01", 25000, 5.0),
                    ("Sade", "2024-04-04", 25000, 5.0),
                    ("Isabel", "2025-08-01", 25000, 5.0),
                ],
            )


def read_table(table: str) -> pd.DataFrame:
    allowed = {"balance_items", "etf_positions", "bitcoin_transactions", "expenses", "family_members", "opa_funds", "opa_transactions"}
    if table not in allowed:
        raise ValueError("Unknown table")
    with connection() as db:
        cursor = db.execute(f"SELECT * FROM {table} ORDER BY id")
        rows = rows_as_dicts(cursor)
        columns = [description[0] for description in cursor.description]
        return pd.DataFrame(rows, columns=columns)


def get_sync_version(table: str) -> int:
    """Geef het versienummer waarmee conflicten tussen apparaten worden herkend."""
    if table not in SYNC_TABLES:
        raise ValueError("Unknown table")
    with connection() as db:
        value = scalar(
            db,
            placeholders("SELECT version FROM sync_state WHERE table_name = ?"),
            (table,),
        )
    return int(value or 0)


def replace_table(
    table: str,
    frame: pd.DataFrame,
    *,
    expected_version: int | None = None,
) -> None:
    allowed = {
        "balance_items": ["category", "name", "amount", "item_type"],
        "etf_positions": ["name", "ticker", "invested", "value"],
        "bitcoin_transactions": ["trade_date", "amount_eur", "btc_amount", "note"],
        "expenses": ["category", "description", "monthly_amount"],
        "family_members": ["name", "relationship", "birth_date", "notes"],
        "opa_funds": ["child_name", "birth_date", "target_amount", "expected_return_pct"],
        "opa_transactions": ["child_name", "transaction_date", "amount", "note"],
    }
    columns = allowed.get(table)
    if not columns:
        raise ValueError("Unknown table")
    clean = validate_table(table, frame)
    with connection() as db:
        now = datetime.now(UTC).isoformat()
        if expected_version is None:
            cursor = db.execute(
                placeholders(
                    """
                    UPDATE sync_state
                    SET version = version + 1, updated_at = ?
                    WHERE table_name = ?
                    """
                ),
                (now, table),
            )
        else:
            cursor = db.execute(
                placeholders(
                    """
                    UPDATE sync_state
                    SET version = version + 1, updated_at = ?
                    WHERE table_name = ? AND version = ?
                    """
                ),
                (now, table, expected_version),
            )
        if cursor.rowcount != 1:
            raise SyncConflictError(
                "Deze gegevens zijn intussen op een ander apparaat gewijzigd. "
                "De nieuwste gegevens zijn opnieuw geladen; voer jouw wijziging "
                "daarna nogmaals in."
            )
        db.execute(f"DELETE FROM {table}")
        if not clean.empty:
            placeholder_marks = ",".join("?" for _ in clean.columns)
            db.executemany(
                placeholders(
                    f"INSERT INTO {table} "
                    f"({','.join(clean.columns)}) VALUES ({placeholder_marks})"
                ),
                clean.where(pd.notna(clean), None).itertuples(index=False, name=None),
            )


def _normalize_date(value: object, label: str, *, optional: bool = False) -> str:
    text = str(value or "").strip()
    if not text and optional:
        return ""
    try:
        return date.fromisoformat(text).isoformat()
    except ValueError as exc:
        raise ValueError(f"{label}: gebruik een geldige datum (JJJJ-MM-DD).") from exc


def _required_text(frame: pd.DataFrame, columns: list[str]) -> None:
    for column in columns:
        frame[column] = frame[column].astype("string").fillna("").str.strip()
        if frame[column].eq("").any():
            raise ValueError(f"Vul het verplichte veld '{column}' in.")


def _numeric(
    frame: pd.DataFrame,
    columns: list[str],
    *,
    allow_zero: bool = True,
    allow_negative: bool = False,
) -> None:
    for column in columns:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
        if frame[column].isna().any():
            raise ValueError(f"Vul bij '{column}' een geldig getal in.")
        if not allow_negative and frame[column].lt(0).any():
            raise ValueError(f"'{column}' mag niet negatief zijn.")
        if not allow_zero and frame[column].eq(0).any():
            raise ValueError(f"'{column}' mag niet nul zijn.")


def validate_table(table: str, frame: pd.DataFrame) -> pd.DataFrame:
    """Verwijder lege invoerregels en controleer alle tabellen vóór opslag."""
    allowed = {
        "balance_items": ["category", "name", "amount", "item_type"],
        "etf_positions": ["name", "ticker", "invested", "value"],
        "bitcoin_transactions": ["trade_date", "amount_eur", "btc_amount", "note"],
        "expenses": ["category", "description", "monthly_amount"],
        "family_members": ["name", "relationship", "birth_date", "notes"],
        "opa_funds": [
            "child_name", "birth_date", "target_amount", "expected_return_pct"
        ],
        "opa_transactions": ["child_name", "transaction_date", "amount", "note"],
    }
    columns = allowed.get(table)
    if not columns:
        raise ValueError("Onbekende tabel.")
    clean = frame.copy()
    for column in columns:
        if column not in clean.columns:
            clean[column] = None
    clean = clean[columns]
    empty = clean.apply(
        lambda row: all(
            pd.isna(value) or str(value).strip() == "" for value in row
        ),
        axis=1,
    )
    clean = clean.loc[~empty].copy().reset_index(drop=True)
    if clean.empty:
        return clean

    if table == "bitcoin_transactions":
        return clean_bitcoin_transactions(clean)
    if table == "balance_items":
        _required_text(clean, ["category", "name", "item_type"])
        _numeric(clean, ["amount"])
        if not clean["item_type"].isin({"asset", "liability"}).all():
            raise ValueError("Type moet 'asset' of 'liability' zijn.")
    elif table == "etf_positions":
        _required_text(clean, ["name", "ticker"])
        _numeric(clean, ["invested", "value"])
    elif table == "expenses":
        _required_text(clean, ["category", "description"])
        _numeric(clean, ["monthly_amount"])
    elif table == "family_members":
        _required_text(clean, ["name", "relationship"])
        clean["notes"] = clean["notes"].astype("string").fillna("").str.strip()
        clean["birth_date"] = [
            _normalize_date(value, "Geboortedatum", optional=True)
            for value in clean["birth_date"]
        ]
    elif table == "opa_funds":
        _required_text(clean, ["child_name"])
        clean["birth_date"] = [
            _normalize_date(value, "Geboortedatum") for value in clean["birth_date"]
        ]
        _numeric(clean, ["target_amount"], allow_zero=False)
        _numeric(clean, ["expected_return_pct"], allow_negative=True)
        if clean["expected_return_pct"].abs().gt(100).any():
            raise ValueError("Verwacht rendement moet tussen -100% en 100% liggen.")
    elif table == "opa_transactions":
        _required_text(clean, ["child_name"])
        clean["note"] = clean["note"].astype("string").fillna("").str.strip()
        clean["transaction_date"] = [
            _normalize_date(value, "Transactiedatum")
            for value in clean["transaction_date"]
        ]
        _numeric(clean, ["amount"], allow_zero=False, allow_negative=True)
    return clean.reset_index(drop=True)


def clean_bitcoin_transactions(frame: pd.DataFrame) -> pd.DataFrame:
    """Verwijder lege regels en valideer Bitcoin-transacties vóór opslag."""
    columns = ["trade_date", "amount_eur", "btc_amount", "note"]
    clean = frame.copy()
    for column in columns:
        if column not in clean.columns:
            clean[column] = None
    clean = clean[columns]

    for column in ("trade_date", "note"):
        clean[column] = clean[column].astype("string").fillna("").str.strip()
    for column in ("amount_eur", "btc_amount"):
        clean[column] = pd.to_numeric(clean[column], errors="coerce")

    completely_empty = (
        clean["trade_date"].eq("")
        & clean["amount_eur"].isna()
        & clean["btc_amount"].isna()
        & clean["note"].eq("")
    )
    clean = clean.loc[~completely_empty].copy()

    if clean.empty:
        return clean.reset_index(drop=True)

    missing_date = clean["trade_date"].eq("")
    if missing_date.any():
        row_numbers = ", ".join(str(index + 1) for index in clean.index[missing_date])
        raise ValueError(
            "Vul bij iedere Bitcoin-transactie een datum in "
            f"(ontbreekt in regel {row_numbers})."
        )

    invalid_dates: list[int] = []
    normalized_dates: list[str] = []
    for index, value in clean["trade_date"].items():
        try:
            normalized_dates.append(date.fromisoformat(str(value)).isoformat())
        except ValueError:
            invalid_dates.append(index + 1)
            normalized_dates.append(str(value))
    if invalid_dates:
        row_numbers = ", ".join(str(number) for number in invalid_dates)
        raise ValueError(
            "Gebruik voor de datum het formaat JJJJ-MM-DD "
            f"(controleer regel {row_numbers})."
        )
    clean["trade_date"] = normalized_dates

    missing_amounts = clean["amount_eur"].isna() | clean["btc_amount"].isna()
    if missing_amounts.any():
        row_numbers = ", ".join(
            str(index + 1) for index in clean.index[missing_amounts]
        )
        raise ValueError(
            "Vul zowel de inleg als het aantal BTC in "
            f"(controleer regel {row_numbers})."
        )

    return clean.reset_index(drop=True)


def get_settings() -> dict[str, str]:
    with connection() as db:
        rows = db.execute("SELECT key,value FROM settings").fetchall()
    return {row["key"]: row["value"] for row in rows}


def set_settings(values: dict[str, object]) -> None:
    with connection() as db:
        db.executemany(
            placeholders("""
            INSERT INTO settings(key,value) VALUES (?,?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value
            """),
            [(key, str(value)) for key, value in values.items()],
        )



def replace_balance_with_freedom_plan(net_cash: float, annuity_reserve: float) -> None:
    """Replace the balance with the planned post-sale allocation."""
    if net_cash < 0 or annuity_reserve < 0:
        raise ValueError("Balansbedragen mogen niet negatief zijn.")
    with connection() as db:
        db.execute(
            placeholders(
                """
                UPDATE sync_state
                SET version = version + 1, updated_at = ?
                WHERE table_name = ?
                """
            ),
            (datetime.now(UTC).isoformat(), "balance_items"),
        )
        db.execute("DELETE FROM balance_items")
        db.executemany(
            placeholders("""
            INSERT INTO balance_items(category,name,amount,item_type)
            VALUES (?,?,?,?)
            """),
            [
                ("Project Vrijheid", "Netto cash na verkoop", net_cash, "asset"),
                ("Project Vrijheid", "Stakingslijfrente", annuity_reserve, "asset"),
            ],
        )


def create_backup() -> Path:
    """Maak een herstelbare back-up voor de actieve databaseprovider."""
    from datetime import datetime
    import json
    import shutil

    backup_dir = Path(__file__).with_name("backups")
    backup_dir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if backend_name() == "sqlite":
        target = backup_dir / f"project_vrijheid_{stamp}.db"
        shutil.copy2(DB_PATH, target)
        return target

    export_dir = backup_dir / f"geertos_cloud_{stamp}"
    export_dir.mkdir()
    tables = [
        "settings",
        "balance_items",
        "etf_positions",
        "bitcoin_transactions",
        "expenses",
        "family_members",
        "opa_funds",
        "opa_transactions",
        "sync_state",
    ]
    manifest: dict[str, object] = {
        "created_at": datetime.now().isoformat(),
        "provider": backend_name(),
        "tables": {},
    }
    with connection() as db:
        for table in tables:
            frame = pd.DataFrame(
                rows_as_dicts(db.execute(f"SELECT * FROM {table} ORDER BY 1"))
            )
            frame.to_csv(export_dir / f"{table}.csv", index=False)
            manifest["tables"][table] = len(frame)
    (export_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    archive = shutil.make_archive(str(export_dir), "zip", export_dir)
    shutil.rmtree(export_dir)
    target = Path(archive)
    validate_backup(target)
    return target


def validate_backup(archive: Path) -> dict[str, object]:
    """Controleer of een cloudback-up compleet en leesbaar is."""
    import csv
    import json
    import zipfile

    required = {
        "settings",
        "balance_items",
        "etf_positions",
        "bitcoin_transactions",
        "expenses",
        "family_members",
        "opa_funds",
        "opa_transactions",
        "sync_state",
    }
    if not archive.exists() or archive.stat().st_size == 0:
        raise ValueError("De back-up bestaat niet of is leeg.")
    with zipfile.ZipFile(archive) as zipped:
        names = set(zipped.namelist())
        if "manifest.json" not in names:
            raise ValueError("De back-up bevat geen manifest.")
        manifest = json.loads(zipped.read("manifest.json"))
        if set(manifest.get("tables", {})) != required:
            raise ValueError("De back-up bevat niet alle vereiste tabellen.")
        for table, expected_count in manifest["tables"].items():
            filename = f"{table}.csv"
            if filename not in names:
                raise ValueError(f"De tabel {table} ontbreekt in de back-up.")
            rows = list(
                csv.reader(zipped.read(filename).decode("utf-8-sig").splitlines())
            )
            if max(0, len(rows) - 1) != int(expected_count):
                raise ValueError(f"De tabel {table} is onvolledig in de back-up.")
    return manifest


def add_opa_transaction(child_name: str, transaction_date: str, amount: float, note: str = "") -> None:
    """Register a deposit or correction in an Opa-fonds."""
    if not child_name.strip():
        raise ValueError("Kies een kleinkind.")
    if amount == 0:
        raise ValueError("Het bedrag mag niet nul zijn.")
    with connection() as db:
        db.execute(
            placeholders(
                """INSERT INTO opa_transactions(
                       child_name,transaction_date,amount,note
                   ) VALUES (?,?,?,?)"""
            ),
            (child_name.strip(), transaction_date, float(amount), note.strip()),
        )
        db.execute(
            placeholders(
                """
                UPDATE sync_state
                SET version = version + 1, updated_at = ?
                WHERE table_name = ?
                """
            ),
            (datetime.now(UTC).isoformat(), "opa_transactions"),
        )
