"""Regressietests voor Sprint 9: persoonlijke financiële waarheid."""

from datetime import date

import pandas as pd
import pytest

from calculations import monthly_income_projection, sale_scenario


def test_bv_sale_separates_vpb_box2_private_and_retained_cash() -> None:
    result = sale_scenario(
        property_price=1_500_000,
        property_book_value=900_000,
        inventory_price=250_000,
        inventory_book_value=200_000,
        mortgage=500_000,
        business_credit=50_000,
        brokerage_pct=1.5,
        tax_pct=40,
        annuity_reserve=0,
        sale_structure="BV",
        vpb_low_pct=19,
        vpb_high_pct=25.8,
        vpb_threshold=200_000,
        box2_pct=31,
        retain_in_bv=100_000,
    )

    assert result["corporate_tax"] > 0
    assert result["income_tax"] == 0
    assert result["box2_tax"] > 0
    assert result["retained_bv"] == 100_000
    assert result["total_after_sale"] == pytest.approx(
        result["net_cash"] + result["retained_bv"]
    )


def test_private_sale_keeps_existing_single_tax_model() -> None:
    result = sale_scenario(
        property_price=1_500_000,
        property_book_value=900_000,
        inventory_price=250_000,
        inventory_book_value=200_000,
        mortgage=500_000,
        business_credit=50_000,
        brokerage_pct=1.5,
        tax_pct=40,
        annuity_reserve=100_000,
    )

    assert result["income_tax"] == pytest.approx(result["taxable_profit"] * 0.40)
    assert result["corporate_tax"] == 0
    assert result["box2_tax"] == 0


def test_exact_start_dates_prorate_first_year() -> None:
    projection = monthly_income_projection(
        birth_date=date(1964, 12, 21),
        start_year=2032,
        end_year=2032,
        target_monthly=4_000,
        inflation_pct=0,
        etf_start=100_000,
        etf_return_pct=0,
        annuity=pd.DataFrame(),
        own_pension_monthly=1_200,
        partner_pension_monthly=600,
        aow_combined_monthly=2_400,
        side_income_monthly=1_200,
        aow_start_date=date(2032, 7, 1),
        own_pension_start_date=date(2032, 4, 1),
        partner_pension_start_date=date(2032, 10, 1),
    )

    row = projection.iloc[0]
    assert row["aow"] == pytest.approx(1_200)
    assert row["side_income"] == pytest.approx(600)
    assert row["pension"] == pytest.approx(1_050)
