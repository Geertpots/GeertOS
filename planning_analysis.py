"""Tijdlijn- en scenariohulpmiddelen boven op de centrale rekenmotor."""

from __future__ import annotations

from typing import Mapping

import pandas as pd


def _number(values: Mapping[str, object], key: str, default: float) -> float:
    try:
        return float(values.get(key, default))
    except (TypeError, ValueError):
        return float(default)


def scenario_definitions(
    settings: Mapping[str, object],
) -> list[dict[str, object]]:
    """Maak drie zichtbare scenario's zonder de opgeslagen planning te wijzigen."""
    price = _number(settings, "sale_property_price", 1_595_000)
    etf_return = _number(settings, "etf_return_pct", 4.0)
    inflation = _number(settings, "inflation_pct", 2.5)
    bitcoin_price = _number(settings, "bitcoin_current_price", 60_000)
    return [
        {
            "name": "Voorzichtig",
            "overrides": {
                "sale_property_price": max(0.0, price - 145_000),
                "etf_return_pct": max(0.0, etf_return - 2.0),
                "inflation_pct": inflation + 1.0,
                "bitcoin_current_price": bitcoin_price * 0.8,
            },
        },
        {
            "name": "Verwacht",
            "overrides": {
                "sale_property_price": price,
                "etf_return_pct": etf_return,
                "inflation_pct": inflation,
                "bitcoin_current_price": bitcoin_price,
            },
        },
        {
            "name": "Optimistisch",
            "overrides": {
                "sale_property_price": price + 105_000,
                "etf_return_pct": etf_return + 2.0,
                "inflation_pct": max(0.0, inflation - 0.5),
                "bitcoin_current_price": bitcoin_price * 1.2,
            },
        },
    ]


def risk_label(result: object) -> str:
    """Vertaal de centrale plancontrole naar een begrijpelijk risicolabel."""
    health = result.projection_health
    if not bool(health["funded"]):
        return "Hoog"
    if float(health["minimum_coverage_pct"]) < 100.0:
        return "Verhoogd"
    if float(health["end_balance"]) < float(result.planned_etf_start) * 0.25:
        return "Middel"
    return "Beheerst"


def compare_scenarios(engine: object, settings: Mapping[str, object]) -> pd.DataFrame:
    """Vergelijk scenario's via FinancialEngine; voer hier geen formules dubbel uit."""
    rows: list[dict[str, object]] = []
    for definition in scenario_definitions(settings):
        overrides = definition["overrides"]
        result = engine.evaluate(overrides)
        last = result.projection.iloc[-1]
        first = result.projection.iloc[0]
        rows.append(
            {
                "Scenario": definition["name"],
                "Verkoopprijs pand": overrides["sale_property_price"],
                "ETF-rendement": overrides["etf_return_pct"],
                "Inflatie": overrides["inflation_pct"],
                "Netto cash": result.sale["net_cash"],
                "Netto vermogen na verkoop": result.post_sale_net_worth,
                "ETF-restvermogen 2047": float(last["etf_closing"]),
                "ETF-opname eerste jaar": float(first["etf_withdrawal"]),
                "Bitcoin-waarde": result.bitcoin_value,
                "Netto inkomen eerste jaar": float(first["actual"]),
                "Vrijheidsstatus": result.freedom_score,
                "Risico": risk_label(result),
            }
        )
    return pd.DataFrame(rows)
