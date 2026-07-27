"""SQLite persistence layer for Project Vrijheid."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path

import pandas as pd


DB_PATH = Path(__file__).with_name("project_vrijheid.db")


@contextmanager
def connection():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    try:
        yield db
        db.commit()
    finally:
        db.close()


def init_db() -> None:
    with connection() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS balance_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                name TEXT NOT NULL,
                amount REAL NOT NULL DEFAULT 0,
                item_type TEXT NOT NULL CHECK(item_type IN ('asset','liability'))
            );
            CREATE TABLE IF NOT EXISTS etf_positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                ticker TEXT NOT NULL,
                invested REAL NOT NULL DEFAULT 0,
                value REAL NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS bitcoin_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_date TEXT NOT NULL,
                amount_eur REAL NOT NULL,
                btc_amount REAL NOT NULL,
                note TEXT DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                monthly_amount REAL NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS family_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                relationship TEXT NOT NULL,
                birth_date TEXT DEFAULT '',
                notes TEXT DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS opa_funds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                child_name TEXT NOT NULL UNIQUE,
                birth_date TEXT NOT NULL,
                target_amount REAL NOT NULL DEFAULT 25000,
                expected_return_pct REAL NOT NULL DEFAULT 5.0
            );
            CREATE TABLE IF NOT EXISTS opa_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                child_name TEXT NOT NULL,
                transaction_date TEXT NOT NULL,
                amount REAL NOT NULL,
                note TEXT DEFAULT ''
            );
            """
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
            "INSERT OR IGNORE INTO settings(key, value) VALUES (?, ?)",
            defaults.items(),
        )

        if db.execute("SELECT COUNT(*) FROM balance_items").fetchone()[0] == 0:
            db.executemany(
                """
                INSERT INTO balance_items(category,name,amount,item_type)
                VALUES (?,?,?,?)
                """,
                [
                    ("Beleggingen", "ETF-portefeuille", 500000, "asset"),
                    ("Buffer", "Spaargeld", 100000, "asset"),
                    ("Lijfrente", "Stakingslijfrente", 250000, "asset"),
                    ("Overig", "Bitcoin", 0, "asset"),
                ],
            )
        if db.execute("SELECT COUNT(*) FROM etf_positions").fetchone()[0] == 0:
            db.executemany(
                """
                INSERT INTO etf_positions(name,ticker,invested,value)
                VALUES (?,?,?,?)
                """,
                [
                    ("Wereldwijde aandelen", "VWCE", 350000, 350000),
                    ("Wereldwijde obligaties", "VAGF", 100000, 100000),
                    ("Geldmarkt / kortlopend", "XEON", 50000, 50000),
                ],
            )
        if db.execute("SELECT COUNT(*) FROM expenses").fetchone()[0] == 0:
            db.executemany(
                """
                INSERT INTO expenses(category,description,monthly_amount)
                VALUES (?,?,?)
                """,
                [
                    ("Wonen", "Woonlasten", 1200),
                    ("Levensonderhoud", "Boodschappen en dagelijks", 900),
                    ("Vrijheid", "Vakantie en genieten", 750),
                    ("Vervoer", "Auto en vervoer", 550),
                    ("Overig", "Verzekeringen en reservering", 600),
                ],
            )

        if db.execute("SELECT COUNT(*) FROM family_members").fetchone()[0] == 0:
            db.executemany(
                """
                INSERT INTO family_members(name,relationship,birth_date,notes)
                VALUES (?,?,?,?)
                """,
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
        if db.execute("SELECT COUNT(*) FROM opa_funds").fetchone()[0] == 0:
            db.executemany(
                """
                INSERT INTO opa_funds(child_name,birth_date,target_amount,expected_return_pct)
                VALUES (?,?,?,?)
                """,
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
        return pd.read_sql_query(f"SELECT * FROM {table} ORDER BY id", db)


def replace_table(table: str, frame: pd.DataFrame) -> None:
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
    clean = frame.copy()
    clean = clean[[c for c in columns if c in clean.columns]]
    with connection() as db:
        db.execute(f"DELETE FROM {table}")
        if not clean.empty:
            placeholders = ",".join("?" for _ in clean.columns)
            db.executemany(
                f"INSERT INTO {table} ({','.join(clean.columns)}) VALUES ({placeholders})",
                clean.where(pd.notna(clean), None).itertuples(index=False, name=None),
            )


def get_settings() -> dict[str, str]:
    with connection() as db:
        rows = db.execute("SELECT key,value FROM settings").fetchall()
    return {row["key"]: row["value"] for row in rows}


def set_settings(values: dict[str, object]) -> None:
    with connection() as db:
        db.executemany(
            """
            INSERT INTO settings(key,value) VALUES (?,?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value
            """,
            [(key, str(value)) for key, value in values.items()],
        )



def replace_balance_with_freedom_plan(net_cash: float, annuity_reserve: float) -> None:
    """Replace the balance with the planned post-sale allocation."""
    if net_cash < 0 or annuity_reserve < 0:
        raise ValueError("Balansbedragen mogen niet negatief zijn.")
    with connection() as db:
        db.execute("DELETE FROM balance_items")
        db.executemany(
            """
            INSERT INTO balance_items(category,name,amount,item_type)
            VALUES (?,?,?,?)
            """,
            [
                ("Project Vrijheid", "Netto cash na verkoop", net_cash, "asset"),
                ("Project Vrijheid", "Stakingslijfrente", annuity_reserve, "asset"),
            ],
        )


def create_backup() -> Path:
    """Create a timestamped copy of the SQLite database next to the app."""
    from datetime import datetime
    import shutil

    backup_dir = Path(__file__).with_name("backups")
    backup_dir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = backup_dir / f"project_vrijheid_{stamp}.db"
    shutil.copy2(DB_PATH, target)
    return target


def add_opa_transaction(child_name: str, transaction_date: str, amount: float, note: str = "") -> None:
    """Register a deposit or correction in an Opa-fonds."""
    if not child_name.strip():
        raise ValueError("Kies een kleinkind.")
    if amount == 0:
        raise ValueError("Het bedrag mag niet nul zijn.")
    with connection() as db:
        db.execute(
            """INSERT INTO opa_transactions(child_name,transaction_date,amount,note)
               VALUES (?,?,?,?)""",
            (child_name.strip(), transaction_date, float(amount), note.strip()),
        )
