"""Stabiliteits- en validatietests voor Sprint 8D."""

from pathlib import Path

import pandas as pd
import pytest

from database import validate_backup, validate_table
from styles import css


def test_empty_editor_rows_are_removed() -> None:
    frame = pd.DataFrame(
        [
            {"name": "Wereld ETF", "ticker": "VWCE", "invested": 100, "value": 110},
            {"name": "", "ticker": "", "invested": None, "value": None},
        ]
    )
    clean = validate_table("etf_positions", frame)
    assert len(clean) == 1
    assert clean.iloc[0]["ticker"] == "VWCE"


def test_invalid_family_date_is_rejected() -> None:
    frame = pd.DataFrame(
        [
            {
                "name": "Test",
                "relationship": "Kind",
                "birth_date": "31-12-2000",
                "notes": "",
            }
        ]
    )
    with pytest.raises(ValueError, match="geldige datum"):
        validate_table("family_members", frame)


def test_negative_financial_value_is_rejected() -> None:
    frame = pd.DataFrame(
        [{"category": "Vast", "description": "Test", "monthly_amount": -1}]
    )
    with pytest.raises(ValueError, match="niet negatief"):
        validate_table("expenses", frame)


def test_invalid_backup_is_rejected(tmp_path: Path) -> None:
    broken = tmp_path / "broken.zip"
    broken.write_bytes(b"geen zip")
    with pytest.raises(Exception):
        validate_backup(broken)


def test_mobile_safety_rules_remain_present() -> None:
    stylesheet = css(False)
    assert "@media (max-width: 700px)" in stylesheet
    assert "overflow-x: auto" in stylesheet
    assert "flex: 1 1 100%" in stylesheet

