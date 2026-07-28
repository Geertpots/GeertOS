"""Gerichte tests voor de tijdlijn- en scenarioanalyse van Sprint 10B."""

from calculations import freedom_index, freedom_index_components
from planning_analysis import compare_scenarios, scenario_definitions
from test_financial_engine import sample_engine


def test_freedom_score_is_composed_from_visible_components() -> None:
    components = freedom_index_components(3_000, 4_000, 500_000, 600_000)

    assert components["budget_weight_pct"] == 55
    assert components["reserve_weight_pct"] == 45
    assert components["total_score"] == freedom_index(
        3_000, 4_000, 500_000, 600_000
    )


def test_scenario_definitions_do_not_change_saved_settings() -> None:
    settings = {
        "sale_property_price": 1_550_000,
        "etf_return_pct": 4.0,
        "inflation_pct": 2.5,
        "bitcoin_current_price": 60_000,
    }
    original = settings.copy()
    definitions = scenario_definitions(settings)

    assert settings == original
    assert [item["name"] for item in definitions] == [
        "Voorzichtig",
        "Verwacht",
        "Optimistisch",
    ]
    assert definitions[1]["overrides"] == original


def test_expected_scenario_matches_the_central_engine() -> None:
    engine = sample_engine()
    comparison = compare_scenarios(engine, engine.settings)
    expected = comparison.loc[comparison["Scenario"] == "Verwacht"].iloc[0]
    baseline = engine.evaluate()

    assert len(comparison) == 3
    assert expected["Netto cash"] == baseline.sale["net_cash"]
    assert (
        expected["Netto vermogen na verkoop"]
        == baseline.post_sale_net_worth
    )
    assert expected["Vrijheidsstatus"] == baseline.freedom_score


def test_scenarios_are_ordered_by_sale_price_and_bitcoin_value() -> None:
    engine = sample_engine()
    comparison = compare_scenarios(engine, engine.settings)

    assert comparison["Verkoopprijs pand"].is_monotonic_increasing
    assert comparison["Bitcoin-waarde"].is_monotonic_increasing
