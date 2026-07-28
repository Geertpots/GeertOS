"""Regressietests voor de centrale financiële rekenmotor van Sprint 8C."""

from datetime import date

import pandas as pd
import pytest

from financial_engine import FinancialEngine


def sample_engine() -> FinancialEngine:
    settings = {
        "sale_property_price": 1_500_000,
        "sale_property_book": 885_000,
        "sale_inventory_price": 275_000,
        "sale_inventory_book": 335_000,
        "sale_mortgage": 675_000,
        "sale_business_credit": 100_000,
        "sale_other_loans": 125_000,
        "sale_brokerage_pct": 1.75,
        "sale_brokerage_vat_pct": 21,
        "sale_tax_pct": 25.8,
        "sale_annuity_reserve": 250_000,
        "safety_buffer": 100_000,
        "bitcoin_current_price": 60_000,
        "birth_date": "1964-12-21",
        "calculation_end_year": 2047,
        "target_monthly": 4_000,
        "inflation_pct": 2.5,
        "etf_return_pct": 4,
        "annuity_years": 15,
        "annuity_return_pct": 2.5,
        "annuity_tax_pct": 37,
        "own_pension_monthly": 145,
        "partner_pension_monthly": 350,
        "aow_combined_monthly": 2_000,
        "side_income_monthly": 1_500,
    }
    balance = pd.DataFrame(
        [
            {"item_type": "asset", "amount": 100_000},
            {"item_type": "liability", "amount": 25_000},
        ]
    )
    etf = pd.DataFrame([{"invested": 40_000, "value": 50_000}])
    bitcoin = pd.DataFrame([{"btc_amount": 0.1}])
    expenses = pd.DataFrame([{"monthly_amount": 3_000}])
    return FinancialEngine(
        settings,
        balance_items=balance,
        etf_positions=etf,
        bitcoin_transactions=bitcoin,
        expenses=expenses,
        today=date(2026, 7, 28),
    )


def test_one_evaluation_supplies_all_cockpit_results() -> None:
    result = sample_engine().evaluate()

    assert result.current_net_worth == 75_000
    assert result.bitcoin_value == 6_000
    assert result.etf["value"] == 50_000
    assert result.annuity_monthly > 0
    assert result.pension_monthly == 2_495
    assert not result.projection.empty
    assert result.post_sale_net_worth == pytest.approx(
        75_000 + result.sale["total_after_sale"]
    )


def test_sale_price_recalculates_all_dependent_results() -> None:
    engine = sample_engine()
    base = engine.evaluate()
    higher = engine.evaluate({"sale_property_price": 1_600_000})

    assert higher.sale["net_cash"] > base.sale["net_cash"]
    assert higher.post_sale_net_worth > base.post_sale_net_worth
    assert higher.planned_etf_start > base.planned_etf_start
    assert (
        higher.projection.iloc[-1]["etf_closing"]
        > base.projection.iloc[-1]["etf_closing"]
    )
    assert higher.annuity_monthly == pytest.approx(base.annuity_monthly)
    assert higher.bitcoin_value == pytest.approx(base.bitcoin_value)


def test_inventory_price_recalculates_all_dependent_results() -> None:
    engine = sample_engine()
    original = engine.settings.copy()
    base = engine.evaluate()
    higher = engine.evaluate({"sale_inventory_price": 350_000})

    assert higher.sale["gross"] > base.sale["gross"]
    assert higher.sale["net_cash"] > base.sale["net_cash"]
    assert higher.post_sale_net_worth > base.post_sale_net_worth
    assert higher.planned_etf_start > base.planned_etf_start
    assert (
        higher.projection.iloc[-1]["etf_closing"]
        > base.projection.iloc[-1]["etf_closing"]
    )
    assert engine.settings == original


def test_complete_sale_scenarios_use_one_central_evaluation() -> None:
    engine = sample_engine()
    comparison = engine.compare_sale_scenarios(
        {
            "Voorzichtig": {
                "sale_property_price": 1_450_000,
                "sale_inventory_price": 250_000,
            },
            "Verwacht": {
                "sale_property_price": 1_500_000,
                "sale_inventory_price": 275_000,
            },
            "Gunstig": {
                "sale_property_price": 1_650_000,
                "sale_inventory_price": 350_000,
            },
        },
        cash_goal=600_000,
    )

    assert comparison["Scenario"].tolist() == [
        "Voorzichtig",
        "Verwacht",
        "Gunstig",
    ]
    assert comparison["Bruto verkoop"].is_monotonic_increasing
    assert comparison["Netto cash"].is_monotonic_increasing
    assert comparison["Vermogen na verkoop"].is_monotonic_increasing
    assert comparison["Vermogen eindjaar"].is_monotonic_increasing


def test_assumption_audit_flags_missing_review_dates() -> None:
    audit = sample_engine().assumption_audit()
    review_rows = audit.loc[audit["Onderdeel"].str.contains("gecontroleerd")]

    assert len(review_rows) == 3
    assert set(review_rows["Status"]) == {"Controleren"}


def test_sale_cash_bridge_reconciles_to_net_cash() -> None:
    sale = sample_engine().evaluate().sale
    cash_after_tax = (
        sale["gross"]
        - sale["total_sale_costs"]
        - sale["total_debt"]
        - sale["tax"]
        - sale["annuity_reserve"]
    )

    assert sale["cash_after_business_tax"] == pytest.approx(cash_after_tax)
    assert sale["net_cash"] == pytest.approx(
        cash_after_tax - sale["retained_bv"] - sale["box2_tax"]
    )


def test_scenario_table_uses_same_sale_calculation() -> None:
    engine = sample_engine()
    table = engine.scenario_table([1_400_000, 1_500_000, 1_600_000])

    expected = engine.sale_result({"sale_property_price": 1_500_000})
    middle = table.loc[table["property_price"] == 1_500_000].iloc[0]
    assert middle["net_cash"] == pytest.approx(expected["net_cash"])
    assert middle["total_after_sale"] == pytest.approx(
        expected["total_after_sale"]
    )
