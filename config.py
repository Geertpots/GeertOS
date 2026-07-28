"""Provider-neutrale configuratie voor GeertOS."""

from __future__ import annotations

import os
from pathlib import Path


def database_url() -> str:
    """Geef de PostgreSQL-URL terug, of een lege tekst voor lokale SQLite."""
    configured = os.getenv("GEERTOS_DATABASE_URL", "").strip()
    if configured:
        return configured

    # Streamlit Community Cloud bewaart productiegeheimen in st.secrets.
    # De optionele import houdt scripts en tests buiten Streamlit bruikbaar.
    try:
        import streamlit as st

        value = str(st.secrets.get("GEERTOS_DATABASE_URL", "")).strip()
        if value:
            return value
    except (ImportError, FileNotFoundError, RuntimeError):
        pass
    return ""


def sqlite_path() -> Path:
    """Bepaal de locatie van de bestaande lokale Sprint 7-database."""
    configured = os.getenv("GEERTOS_DB_PATH", "").strip()
    path = (
        Path(configured).expanduser()
        if configured
        else Path(__file__).with_name("project_vrijheid.db")
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    return path.resolve()

