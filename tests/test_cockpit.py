"""Tests voor Sprint 10A: de dagelijkse intelligente cockpit."""

from datetime import datetime
from types import SimpleNamespace

from cockpit import daily_insights, greeting, plan_status


def result(*, funded: bool = True, end_balance: float = 200_000) -> object:
    return SimpleNamespace(
        projection_health={
            "funded": funded,
            "first_shortfall_year": 2038 if not funded else 0,
            "end_balance": end_balance,
            "minimum_coverage_pct": 82.5 if not funded else 100.0,
        },
        sale={"net_cash": 650_000},
        etf={"value": 100_000},
        bitcoin_value=10_000,
    )


def test_greeting_follows_time_of_day() -> None:
    assert greeting(datetime(2026, 7, 28, 8, 0)) == "Goedemorgen"
    assert greeting(datetime(2026, 7, 28, 14, 0)) == "Goedemiddag"
    assert greeting(datetime(2026, 7, 28, 20, 0)) == "Goedenavond"


def test_status_is_on_track_when_income_and_buffer_are_healthy() -> None:
    status = plan_status(result(), {"safety_buffer": 100_000})
    assert status["label"] == "Op koers"


def test_shortfall_is_the_highest_priority_insight() -> None:
    insights = daily_insights(
        result(funded=False, end_balance=0),
        {
            "safety_buffer": 100_000,
            "sale_net_cash_goal": 600_000,
            "birth_date": "1964-12-21",
            "aow_start_date": "2032-03-21",
            "own_pension_start_date": "2032-03-21",
            "annuity_start_date": "2026-01-01",
        },
    )
    assert insights[0].level == "error"
    assert "2038" in insights[0].title


def test_insights_are_limited_and_do_not_change_data() -> None:
    settings = {
        "safety_buffer": 300_000,
        "sale_net_cash_goal": 700_000,
    }
    original = dict(settings)
    insights = daily_insights(result(end_balance=100_000), settings, limit=2)
    assert len(insights) == 2
    assert settings == original
