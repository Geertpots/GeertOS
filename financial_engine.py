"""Centrale, UI- en provider-onafhankelijke rekenmotor voor GeertOS."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Mapping

import pandas as pd

from calculations import (
    annuity_schedule,
    freedom_index,
    monthly_income_projection,
    portfolio_summary,
    projection_health,
    sale_scenario,
    sale_scenario_table,
    stress_test_income_plan,
)


def _number(values: Mapping[str, object], key: str, default: float) -> float:
    try:
        return float(values.get(key, default))
    except (TypeError, ValueError):
        return float(default)


def _integer(values: Mapping[str, object], key: str, default: int) -> int:
    return int(_number(values, key, float(default)))


def _date_value(values: Mapping[str, object], key: str, default: date) -> date:
    try:
        return date.fromisoformat(str(values.get(key, default.isoformat())))
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class FinancialResult:
    """Alle onderling samenhangende uitkomsten van één financieel scenario."""

    sale: dict[str, float]
    annuity: pd.DataFrame
    projection: pd.DataFrame
    projection_health: dict[str, float | int | bool]
    etf: dict[str, float]
    current_net_worth: float
    post_sale_net_worth: float
    bitcoin_amount: float
    bitcoin_value: float
    pension_monthly: float
    annuity_monthly: float
    expenses_monthly: float
    planned_etf_start: float
    freedom_score: int


class FinancialEngine:
    """Bereken alle cockpituitkomsten vanuit één consistente invoerset."""

    def __init__(
        self,
        settings: Mapping[str, object],
        *,
        balance_items: pd.DataFrame,
        etf_positions: pd.DataFrame,
        bitcoin_transactions: pd.DataFrame,
        expenses: pd.DataFrame,
        today: date | None = None,
    ) -> None:
        self.settings = dict(settings)
        self.balance_items = balance_items.copy()
        self.etf_positions = etf_positions.copy()
        self.bitcoin_transactions = bitcoin_transactions.copy()
        self.expenses = expenses.copy()
        self.today = today or date.today()

    def _values(self, overrides: Mapping[str, object] | None) -> dict[str, object]:
        values = dict(self.settings)
        if overrides:
            values.update(overrides)
        return values

    def sale_result(
        self, overrides: Mapping[str, object] | None = None
    ) -> dict[str, float]:
        values = self._values(overrides)
        return sale_scenario(
            property_price=_number(values, "sale_property_price", 1_595_000),
            property_book_value=_number(values, "sale_property_book", 885_000),
            inventory_price=_number(values, "sale_inventory_price", 275_000),
            inventory_book_value=_number(values, "sale_inventory_book", 335_000),
            mortgage=_number(values, "sale_mortgage", 675_000),
            business_credit=_number(values, "sale_business_credit", 100_000),
            brokerage_pct=_number(values, "sale_brokerage_pct", 1.75),
            tax_pct=_number(values, "sale_tax_pct", 25.8),
            annuity_reserve=_number(values, "sale_annuity_reserve", 250_000),
            other_loans=_number(values, "sale_other_loans", 125_000),
            brokerage_vat_pct=_number(values, "sale_brokerage_vat_pct", 21),
            other_sale_costs=_number(values, "sale_other_costs", 0),
            sale_structure=str(values.get("sale_structure", "Privé/eenmanszaak")),
            vpb_low_pct=_number(values, "sale_vpb_low_pct", 19),
            vpb_high_pct=_number(values, "sale_vpb_high_pct", 25.8),
            vpb_threshold=_number(values, "sale_vpb_threshold", 200_000),
            box2_pct=_number(values, "sale_box2_pct", 31),
            retain_in_bv=_number(values, "sale_retain_in_bv", 0),
        )

    def scenario_table(self, property_prices: list[float]) -> pd.DataFrame:
        values = self.settings
        return sale_scenario_table(
            property_prices,
            property_book_value=_number(values, "sale_property_book", 885_000),
            inventory_price=_number(values, "sale_inventory_price", 275_000),
            inventory_book_value=_number(values, "sale_inventory_book", 335_000),
            mortgage=_number(values, "sale_mortgage", 675_000),
            business_credit=_number(values, "sale_business_credit", 100_000),
            brokerage_pct=_number(values, "sale_brokerage_pct", 1.75),
            tax_pct=_number(values, "sale_tax_pct", 25.8),
            annuity_reserve=_number(values, "sale_annuity_reserve", 250_000),
            other_loans=_number(values, "sale_other_loans", 125_000),
            brokerage_vat_pct=_number(values, "sale_brokerage_vat_pct", 21),
            other_sale_costs=_number(values, "sale_other_costs", 0),
            sale_structure=str(values.get("sale_structure", "Privé/eenmanszaak")),
            vpb_low_pct=_number(values, "sale_vpb_low_pct", 19),
            vpb_high_pct=_number(values, "sale_vpb_high_pct", 25.8),
            vpb_threshold=_number(values, "sale_vpb_threshold", 200_000),
            box2_pct=_number(values, "sale_box2_pct", 31),
            retain_in_bv=_number(values, "sale_retain_in_bv", 0),
        )

    def evaluate(
        self, overrides: Mapping[str, object] | None = None
    ) -> FinancialResult:
        values = self._values(overrides)
        sale = self.sale_result(overrides)

        assets = (
            float(
                self.balance_items.loc[
                    self.balance_items["item_type"] == "asset", "amount"
                ].sum()
            )
            if not self.balance_items.empty
            else 0.0
        )
        debts = (
            float(
                self.balance_items.loc[
                    self.balance_items["item_type"] == "liability", "amount"
                ].sum()
            )
            if not self.balance_items.empty
            else 0.0
        )
        current_net_worth = assets - debts
        etf = portfolio_summary(self.etf_positions)
        bitcoin_amount = (
            float(self.bitcoin_transactions["btc_amount"].sum())
            if not self.bitcoin_transactions.empty
            else 0.0
        )
        bitcoin_value = bitcoin_amount * _number(
            values, "bitcoin_current_price", 60_000
        )
        expenses_monthly = (
            float(self.expenses["monthly_amount"].sum())
            if not self.expenses.empty
            else 0.0
        )

        # De verkoopopbrengst, bestaande ETF-waarde en buffer vormen samen één
        # bron voor alle toekomstige vermogens- en inkomensberekeningen.
        planned_etf_start = max(
            0.0,
            float(etf["value"])
            + float(sale["net_cash"])
            - _number(values, "safety_buffer", 100_000),
        )
        annuity_start = _date_value(
            values, "annuity_start_date", date(self.today.year, 1, 1)
        )
        annuity = annuity_schedule(
            principal=float(sale["annuity_reserve"]),
            years=_integer(values, "annuity_years", 15),
            annual_return_pct=_number(values, "annuity_return_pct", 2.5),
            tax_pct=_number(values, "annuity_tax_pct", 37),
            start_year=annuity_start.year,
        )
        projection = monthly_income_projection(
            birth_date=date.fromisoformat(
                str(values.get("birth_date", "1964-12-21"))
            ),
            start_year=self.today.year,
            end_year=_integer(values, "calculation_end_year", 2047),
            target_monthly=_number(values, "target_monthly", 4_000),
            inflation_pct=_number(values, "inflation_pct", 2.5),
            etf_start=planned_etf_start,
            etf_return_pct=_number(values, "etf_return_pct", 4),
            annuity=annuity,
            own_pension_monthly=_number(values, "own_pension_monthly", 145),
            partner_pension_monthly=_number(
                values, "partner_pension_monthly", 350
            ),
            aow_combined_monthly=_number(
                values, "aow_combined_monthly", 2_000
            ),
            side_income_monthly=_number(values, "side_income_monthly", 1_500),
            aow_start_date=_date_value(
                values, "aow_start_date", date(2032, 3, 21)
            ),
            own_pension_start_date=_date_value(
                values, "own_pension_start_date", date(2032, 3, 21)
            ),
            partner_pension_start_date=_date_value(
                values, "partner_pension_start_date", date(2032, 3, 21)
            ),
            annuity_start_date=annuity_start,
        )
        pension_monthly = (
            _number(values, "own_pension_monthly", 145)
            + _number(values, "partner_pension_monthly", 350)
            + _number(values, "aow_combined_monthly", 2_000)
        )
        annuity_monthly = (
            float(annuity.iloc[0]["net_monthly"]) if not annuity.empty else 0.0
        )
        health = projection_health(projection)
        score = freedom_index(
            expenses_monthly,
            _number(values, "target_monthly", 4_000),
            float(health["end_balance"]),
            max(planned_etf_start, 1.0),
        )
        return FinancialResult(
            sale=sale,
            annuity=annuity,
            projection=projection,
            projection_health=health,
            etf=etf,
            current_net_worth=current_net_worth,
            post_sale_net_worth=current_net_worth + sale["total_after_sale"],
            bitcoin_amount=bitcoin_amount,
            bitcoin_value=bitcoin_value,
            pension_monthly=pension_monthly,
            annuity_monthly=annuity_monthly,
            expenses_monthly=expenses_monthly,
            planned_etf_start=planned_etf_start,
            freedom_score=score,
        )

    def stress_table(
        self,
        return_scenarios: tuple[float, ...] = (2.0, 4.0, 6.0),
    ) -> pd.DataFrame:
        result = self.evaluate()
        values = self.settings
        return stress_test_income_plan(
            birth_date=date.fromisoformat(
                str(values.get("birth_date", "1964-12-21"))
            ),
            start_year=self.today.year,
            end_year=_integer(values, "calculation_end_year", 2047),
            target_monthly=_number(values, "target_monthly", 4_000),
            inflation_pct=_number(values, "inflation_pct", 2.5),
            etf_start=result.planned_etf_start,
            annuity=result.annuity,
            own_pension_monthly=_number(values, "own_pension_monthly", 145),
            partner_pension_monthly=_number(
                values, "partner_pension_monthly", 350
            ),
            aow_combined_monthly=_number(
                values, "aow_combined_monthly", 2_000
            ),
            side_income_monthly=_number(values, "side_income_monthly", 1_500),
            aow_start_date=_date_value(
                values, "aow_start_date", date(2032, 3, 21)
            ),
            own_pension_start_date=_date_value(
                values, "own_pension_start_date", date(2032, 3, 21)
            ),
            partner_pension_start_date=_date_value(
                values, "partner_pension_start_date", date(2032, 3, 21)
            ),
            annuity_start_date=_date_value(
                values, "annuity_start_date", date(self.today.year, 1, 1)
            ),
            return_scenarios=return_scenarios,
        )
