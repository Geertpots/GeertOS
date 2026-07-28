"""Tests voor de veilige financiële adviseur van Sprint 10C."""

from advisor import answer_question
from test_financial_engine import sample_engine


def test_sale_question_uses_central_engine_without_changing_settings() -> None:
    engine = sample_engine()
    original = engine.settings.copy()
    answer = answer_question(
        "Wat gebeurt er als het pand € 1.575.000 oplevert?",
        engine,
        engine.settings,
    )

    assert answer.title == "Verkoopscenario POTZ WONEN"
    assert "€ 1.575.000" in answer.message
    assert engine.settings == original


def test_bitcoin_drop_is_explained_without_projecting_growth() -> None:
    engine = sample_engine()
    answer = answer_question(
        "Wat gebeurt er als Bitcoin 20% daalt?", engine, engine.settings
    )

    assert answer.title == "Bitcoin-scenario"
    assert "20,0%" in answer.message
    assert any("pensioenprojectie" in item.lower() for item in answer.details)


def test_bitcoin_rise_is_understood_too() -> None:
    engine = sample_engine()
    answer = answer_question(
        "Wat als Bitcoin 20% stijgt?", engine, engine.settings
    )

    assert answer.title == "Bitcoin-scenario"
    assert "stijging van 20,0%" in answer.message
    assert answer.level == "success"


def test_large_purchase_returns_a_planning_assessment() -> None:
    engine = sample_engine()
    answer = answer_question(
        "Kan ik veilig € 80.000 aan een camper besteden?",
        engine,
        engine.settings,
    )

    assert answer.title == "Gevolg voor je plan"
    assert "€ 80.000" in answer.message
    assert answer.destination == "Beslislab"


def test_unknown_question_explains_supported_scope() -> None:
    engine = sample_engine()
    answer = answer_question(
        "Wat zal het morgen voor weer zijn?", engine, engine.settings
    )

    assert answer.level == "info"
    assert answer.destination == "Vandaag"
