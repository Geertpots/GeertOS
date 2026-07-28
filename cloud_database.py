"""Kleine database-adapter voor SQLite en standaard PostgreSQL."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Any, Iterator

from config import database_url, sqlite_path


class CompatiblePostgresConnection:
    """Bied de kleine SQLite-interface die de bestaande app verwacht."""

    def __init__(self, raw: Any) -> None:
        self.raw = raw

    def execute(self, sql: str, params: tuple[object, ...] = ()) -> Any:
        return self.raw.execute(sql, params)

    def executemany(self, sql: str, rows: Any) -> Any:
        cursor = self.raw.cursor()
        cursor.executemany(sql, rows)
        return cursor

    def commit(self) -> None:
        self.raw.commit()

    def rollback(self) -> None:
        self.raw.rollback()

    def close(self) -> None:
        self.raw.close()


def backend_name() -> str:
    return "postgresql" if database_url() else "sqlite"


def placeholders(sql: str) -> str:
    """Vertaal veilige qmark-parameters naar PostgreSQL-parameters."""
    return sql.replace("?", "%s") if backend_name() == "postgresql" else sql


@contextmanager
def connection() -> Iterator[Any]:
    """Open één transactionele verbinding met de ingestelde database."""
    if backend_name() == "postgresql":
        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError as exc:
            raise RuntimeError(
                "PostgreSQL is ingesteld, maar psycopg ontbreekt. "
                "Installeer eerst de onderdelen uit requirements.txt."
            ) from exc
        db = CompatiblePostgresConnection(
            psycopg.connect(
                database_url(),
                row_factory=dict_row,
                prepare_threshold=None,
            )
        )
    else:
        db = sqlite3.connect(sqlite_path())
        db.row_factory = sqlite3.Row

    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def scalar(db: Any, sql: str, params: tuple[object, ...] = ()) -> object:
    row = db.execute(placeholders(sql), params).fetchone()
    if row is None:
        return None
    if isinstance(row, dict):
        return next(iter(row.values()))
    return row[0]


def rows_as_dicts(cursor: Any) -> list[dict[str, object]]:
    rows = cursor.fetchall()
    return [dict(row) for row in rows]
