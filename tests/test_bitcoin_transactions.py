"""Regressietests voor het opslaan van Bitcoin-transacties."""

from __future__ import annotations

import pandas as pd
import pytest

from database import clean_bitcoin_transactions


def test_completely_empty_rows_are_removed() -> None:
    frame = pd.DataFrame(
        [
            {
                "trade_date": "2026-07-27",
                "amount_eur": 250.0,
                "btc_amount": 0.0025,
                "note": "Aankoop",
            },
            {
                "trade_date": None,
                "amount_eur": None,
                "btc_amount": None,
                "note": None,
            },
        ]
    )

    result = clean_bitcoin_transactions(frame)

    assert len(result) == 1
    assert result.iloc[0]["trade_date"] == "2026-07-27"


def test_partially_filled_row_requires_date() -> None:
    frame = pd.DataFrame(
        [
            {
                "trade_date": "",
                "amount_eur": 250.0,
                "btc_amount": 0.0025,
                "note": "",
            }
        ]
    )

    with pytest.raises(ValueError, match="datum"):
        clean_bitcoin_transactions(frame)


def test_existing_transaction_can_be_modified() -> None:
    frame = pd.DataFrame(
        [
            {
                "trade_date": "2026-07-27",
                "amount_eur": 300.0,
                "btc_amount": 0.003,
                "note": "Gewijzigd",
            }
        ]
    )

    result = clean_bitcoin_transactions(frame)

    assert result.to_dict("records") == [
        {
            "trade_date": "2026-07-27",
            "amount_eur": 300.0,
            "btc_amount": 0.003,
            "note": "Gewijzigd",
        }
    ]
