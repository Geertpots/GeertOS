"""Pure financial calculations for Project Vrijheid.

The functions in this module do not know anything about Streamlit or SQLite.
That makes them easy to test and reuse.
"""

from __future__ import annotations

from datetime import date
from typing import Iterable

import pandas as pd


def money(value: float) -> str:
    """Format a value as Dutch-style whole euros."""
    return f"€ {value:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")


def net_worth(assets: Iterable[float], liabilities: Iterable[float]) -> float:
    return float(sum(assets) - sum(liabilities))


def portfolio_summary(rows: pd.DataFrame) -> dict[str, float]:
    if rows.empty:
        return {"invested": 0.0, "value": 0.0, "result": 0.0, "return_pct": 0.0}
    invested = float(rows["invested"].sum())
    value = float(rows["value"].sum())
    result = value - invested
    return {
        "invested": invested,
        "value": value,
        "result": result,
        "return_pct": (result / invested * 100) if invested else 0.0,
    }


def annuity_schedule(
    principal: float,
    years: int,
    annual_return_pct: float,
    tax_pct: float,
    start_year: int,
) -> pd.DataFrame:
    """Create an annual level-payment annuity schedule."""
    years = max(int(years), 1)
    rate = annual_return_pct / 100
    gross_payment = (
        principal / years
        if rate == 0
        else principal * rate / (1 - (1 + rate) ** -years)
    )
    balance = float(principal)
    rows = []
    for offset in range(years):
        interest = balance * rate
        principal_paid = min(balance, max(0.0, gross_payment - interest))
        balance = max(0.0, balance - principal_paid)
        gross = interest + principal_paid
        net = gross * (1 - tax_pct / 100)
        rows.append(
            {
                "year": start_year + offset,
                "opening": balance + principal_paid,
                "interest": interest,
                "gross": gross,
                "net": net,
                "net_monthly": net / 12,
                "closing": balance,
            }
        )
    return pd.DataFrame(rows)


def sale_scenario(
    property_price: float,
    property_book_value: float,
    inventory_price: float,
    inventory_book_value: float,
    mortgage: float,
    business_credit: float,
    brokerage_pct: float,
    tax_pct: float,
    annuity_reserve: float,
    other_loans: float = 0.0,
    brokerage_vat_pct: float = 21.0,
    other_sale_costs: float = 0.0,
) -> dict[str, float]:
    """Calculate an indicative company-sale result.

    Brokerage is calculated over the property price and increased with VAT.
    Tax is calculated over positive book profit after sale costs and after the
    entered annuity reserve. This is a planning model, not a tax return.
    """
    values = {
        "property_price": property_price,
        "property_book_value": property_book_value,
        "inventory_price": inventory_price,
        "inventory_book_value": inventory_book_value,
        "mortgage": mortgage,
        "business_credit": business_credit,
        "other_loans": other_loans,
        "brokerage_pct": brokerage_pct,
        "brokerage_vat_pct": brokerage_vat_pct,
        "tax_pct": tax_pct,
        "annuity_reserve": annuity_reserve,
        "other_sale_costs": other_sale_costs,
    }
    if any(value < 0 for value in values.values()):
        raise ValueError("Bedragen en percentages mogen niet negatief zijn.")

    gross = property_price + inventory_price
    brokerage_ex_vat = property_price * brokerage_pct / 100
    brokerage_vat = brokerage_ex_vat * brokerage_vat_pct / 100
    brokerage = brokerage_ex_vat + brokerage_vat
    total_sale_costs = brokerage + other_sale_costs
    total_debt = mortgage + business_credit + other_loans

    book_profit = max(
        0.0,
        property_price
        - property_book_value
        + inventory_price
        - inventory_book_value
        - total_sale_costs,
    )
    taxable_profit = max(0.0, book_profit - annuity_reserve)
    tax = taxable_profit * tax_pct / 100
    net_cash = gross - total_sale_costs - total_debt - tax - annuity_reserve
    total_after_sale = net_cash + annuity_reserve

    return {
        "gross": gross,
        "brokerage_ex_vat": brokerage_ex_vat,
        "brokerage_vat": brokerage_vat,
        "brokerage": brokerage,
        "other_sale_costs": other_sale_costs,
        "total_sale_costs": total_sale_costs,
        "total_debt": total_debt,
        "book_profit": book_profit,
        "taxable_profit": taxable_profit,
        "tax": tax,
        "annuity_reserve": annuity_reserve,
        "net_cash": net_cash,
        "total_after_sale": total_after_sale,
    }



def sale_scenario_table(
    property_prices: Iterable[float],
    *,
    property_book_value: float,
    inventory_price: float,
    inventory_book_value: float,
    mortgage: float,
    business_credit: float,
    brokerage_pct: float,
    tax_pct: float,
    annuity_reserve: float,
    other_loans: float = 0.0,
    brokerage_vat_pct: float = 21.0,
    other_sale_costs: float = 0.0,
) -> pd.DataFrame:
    """Return a comparable table for multiple property sale prices."""
    rows: list[dict[str, float]] = []
    for property_price in property_prices:
        result = sale_scenario(
            property_price=property_price,
            property_book_value=property_book_value,
            inventory_price=inventory_price,
            inventory_book_value=inventory_book_value,
            mortgage=mortgage,
            business_credit=business_credit,
            brokerage_pct=brokerage_pct,
            tax_pct=tax_pct,
            annuity_reserve=annuity_reserve,
            other_loans=other_loans,
            brokerage_vat_pct=brokerage_vat_pct,
            other_sale_costs=other_sale_costs,
        )
        rows.append(
            {
                "property_price": float(property_price),
                "gross": result["gross"],
                "sale_costs": result["total_sale_costs"],
                "debt": result["total_debt"],
                "tax": result["tax"],
                "annuity": result["annuity_reserve"],
                "net_cash": result["net_cash"],
                "total_after_sale": result["total_after_sale"],
            }
        )
    return pd.DataFrame(rows)


def freedom_index(
    monthly_expenses: float,
    monthly_target: float,
    projected_end_balance: float,
    starting_investments: float,
) -> int:
    """Calculate a transparent 0-100 planning score."""
    target = max(float(monthly_target), 1.0)
    start = max(float(starting_investments), 1.0)
    budget_score = max(0.0, min(100.0, 100.0 - abs(monthly_expenses - target) / target * 100.0))
    reserve_score = max(0.0, min(100.0, projected_end_balance / start * 100.0))
    return round(0.55 * budget_score + 0.45 * reserve_score)

def monthly_income_projection(
    birth_date: date,
    start_year: int,
    end_year: int,
    target_monthly: float,
    inflation_pct: float,
    etf_start: float,
    etf_return_pct: float,
    annuity: pd.DataFrame,
    own_pension_monthly: float,
    partner_pension_monthly: float,
    aow_combined_monthly: float,
    side_income_monthly: float,
    aow_age_years: int = 67,
    aow_age_months: int = 3,
) -> pd.DataFrame:
    """Project sources and required ETF withdrawals through end_year."""
    aow_year = birth_date.year + aow_age_years
    if birth_date.month + aow_age_months > 12:
        aow_year += 1

    annuity_by_year = (
        annuity.set_index("year")["net_monthly"].to_dict()
        if not annuity.empty
        else {}
    )
    balance = float(etf_start)
    rows: list[dict[str, float]] = []
    for year in range(start_year, end_year + 1):
        target = target_monthly * (1 + inflation_pct / 100) ** (year - start_year)
        aow_active = year >= aow_year
        pension = (
            own_pension_monthly + partner_pension_monthly if aow_active else 0.0
        )
        aow = aow_combined_monthly if aow_active else 0.0
        side_income = side_income_monthly if not aow_active else 0.0
        annuity_income = float(annuity_by_year.get(year, 0.0))
        other_income = pension + aow + side_income + annuity_income
        required = max(0.0, target - other_income)

        investment_return = balance * etf_return_pct / 100
        withdrawal = min(balance + investment_return, required * 12)
        balance = max(0.0, balance + investment_return - withdrawal)
        actual = other_income + withdrawal / 12
        rows.append(
            {
                "year": year,
                "target": target,
                "annuity": annuity_income,
                "aow": aow,
                "pension": pension,
                "side_income": side_income,
                "etf_withdrawal": withdrawal / 12,
                "actual": actual,
                "etf_closing": balance,
            }
        )
    return pd.DataFrame(rows)



def projection_health(projection: pd.DataFrame) -> dict[str, float | int | bool]:
    """Summarise whether a projected income plan remains funded."""
    if projection.empty:
        return {
            "funded": False,
            "first_shortfall_year": 0,
            "end_balance": 0.0,
            "total_withdrawals": 0.0,
            "minimum_coverage_pct": 0.0,
        }

    coverage = projection.apply(
        lambda row: (float(row["actual"]) / float(row["target"]) * 100)
        if float(row["target"]) > 0
        else 100.0,
        axis=1,
    )
    shortfall_rows = projection.loc[coverage < 99.999]
    first_shortfall = int(shortfall_rows.iloc[0]["year"]) if not shortfall_rows.empty else 0
    return {
        "funded": shortfall_rows.empty,
        "first_shortfall_year": first_shortfall,
        "end_balance": float(projection.iloc[-1]["etf_closing"]),
        "total_withdrawals": float(projection["etf_withdrawal"].sum() * 12),
        "minimum_coverage_pct": float(coverage.min()),
    }


def stress_test_income_plan(
    *,
    birth_date: date,
    start_year: int,
    end_year: int,
    target_monthly: float,
    inflation_pct: float,
    etf_start: float,
    annuity: pd.DataFrame,
    own_pension_monthly: float,
    partner_pension_monthly: float,
    aow_combined_monthly: float,
    side_income_monthly: float,
    return_scenarios: Iterable[float] = (2.0, 4.0, 6.0),
) -> pd.DataFrame:
    """Compare the same plan under several annual ETF return assumptions."""
    rows: list[dict[str, float | int | bool]] = []
    for annual_return in return_scenarios:
        projection = monthly_income_projection(
            birth_date=birth_date,
            start_year=start_year,
            end_year=end_year,
            target_monthly=target_monthly,
            inflation_pct=inflation_pct,
            etf_start=etf_start,
            etf_return_pct=float(annual_return),
            annuity=annuity,
            own_pension_monthly=own_pension_monthly,
            partner_pension_monthly=partner_pension_monthly,
            aow_combined_monthly=aow_combined_monthly,
            side_income_monthly=side_income_monthly,
        )
        health = projection_health(projection)
        rows.append(
            {
                "return_pct": float(annual_return),
                "funded": bool(health["funded"]),
                "first_shortfall_year": int(health["first_shortfall_year"]),
                "end_balance": float(health["end_balance"]),
                "total_withdrawals": float(health["total_withdrawals"]),
                "minimum_coverage_pct": float(health["minimum_coverage_pct"]),
            }
        )
    return pd.DataFrame(rows)


def monte_carlo_income_plan(
    projection: pd.DataFrame,
    *,
    starting_capital: float,
    expected_return_pct: float,
    volatility_pct: float,
    simulations: int = 2000,
    one_time_cost: float = 0.0,
    extra_monthly_spending: float = 0.0,
    inflation_pct: float = 0.0,
    seed: int = 42,
) -> tuple[dict[str, float | int], pd.DataFrame]:
    """Run a deterministic Monte Carlo stress test over an income projection.

    The projection supplies the non-investment income for every year. Random
    annual ETF returns are drawn from a normal distribution. A simulation is
    successful when the ETF portfolio can fund every annual shortfall through
    the final projection year.
    """
    import random

    if projection.empty:
        return (
            {
                "success_probability": 0.0,
                "median_end_balance": 0.0,
                "p10_end_balance": 0.0,
                "p90_end_balance": 0.0,
                "simulations": 0,
            },
            pd.DataFrame(columns=["year", "p10", "median", "p90"]),
        )
    if starting_capital < 0 or one_time_cost < 0 or extra_monthly_spending < 0:
        raise ValueError("Bedragen mogen niet negatief zijn.")
    if simulations < 100 or simulations > 20_000:
        raise ValueError("Aantal simulaties moet tussen 100 en 20.000 liggen.")
    if volatility_pct < 0:
        raise ValueError("Volatiliteit mag niet negatief zijn.")

    rng = random.Random(seed)
    years = [int(value) for value in projection["year"].tolist()]
    first_year = years[0]
    balances_by_year: list[list[float]] = [[] for _ in years]
    ending_balances: list[float] = []
    successful = 0

    for _ in range(int(simulations)):
        balance = max(0.0, float(starting_capital) - float(one_time_cost))
        funded = True
        for index, (_, row) in enumerate(projection.iterrows()):
            return_rate = rng.gauss(
                float(expected_return_pct) / 100.0,
                float(volatility_pct) / 100.0,
            )
            balance = max(0.0, balance * (1.0 + return_rate))

            other_income_monthly = float(
                row["annuity"] + row["aow"] + row["pension"] + row["side_income"]
            )
            extra = float(extra_monthly_spending) * (
                1.0 + float(inflation_pct) / 100.0
            ) ** (int(row["year"]) - first_year)
            required_annual = max(
                0.0,
                (float(row["target"]) + extra - other_income_monthly) * 12.0,
            )
            if required_annual > balance + 1e-9:
                funded = False
                balance = 0.0
            else:
                balance -= required_annual
            balances_by_year[index].append(balance)

        ending_balances.append(balance)
        if funded:
            successful += 1

    def percentile(values: list[float], fraction: float) -> float:
        ordered = sorted(values)
        if not ordered:
            return 0.0
        position = (len(ordered) - 1) * fraction
        lower = int(position)
        upper = min(lower + 1, len(ordered) - 1)
        weight = position - lower
        return ordered[lower] * (1.0 - weight) + ordered[upper] * weight

    path_rows = []
    for year, values in zip(years, balances_by_year):
        path_rows.append(
            {
                "year": year,
                "p10": percentile(values, 0.10),
                "median": percentile(values, 0.50),
                "p90": percentile(values, 0.90),
            }
        )

    summary: dict[str, float | int] = {
        "success_probability": successful / simulations * 100.0,
        "median_end_balance": percentile(ending_balances, 0.50),
        "p10_end_balance": percentile(ending_balances, 0.10),
        "p90_end_balance": percentile(ending_balances, 0.90),
        "simulations": int(simulations),
    }
    return summary, pd.DataFrame(path_rows)


def decision_label(success_probability: float) -> tuple[str, str]:
    """Return a concise Dutch decision label and explanation."""
    probability = float(success_probability)
    if probability >= 90:
        return "Sterk", "De gekozen uitgave past ruim binnen de simulaties."
    if probability >= 75:
        return "Haalbaar", "De uitgave lijkt haalbaar, met beperkte veiligheidsmarge."
    if probability >= 60:
        return "Aandacht", "De uitgave kan, maar maakt je plan merkbaar kwetsbaarder."
    return "Onvoldoende", "De kans op volledige dekking is te laag voor een robuust plan."
