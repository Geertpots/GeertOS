"""Betrouwbare, provider-onafhankelijke cockpitinzichten voor GeertOS."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Mapping


@dataclass(frozen=True)
class CockpitInsight:
    """Eén controleerbaar aandachtspunt voor de pagina Vandaag."""

    priority: int
    level: str
    title: str
    message: str
    destination: str


def greeting(moment: datetime) -> str:
    """Geef een persoonlijke begroeting passend bij het tijdstip."""
    if moment.hour < 12:
        return "Goedemorgen"
    if moment.hour < 18:
        return "Goedemiddag"
    return "Goedenavond"


def plan_status(result: object, settings: Mapping[str, object]) -> dict[str, str]:
    """Vat de financiële gezondheid transparant samen."""
    health = result.projection_health
    end_balance = float(health["end_balance"])
    buffer_goal = float(settings.get("safety_buffer", 0) or 0)

    if not bool(health["funded"]):
        year = int(health["first_shortfall_year"])
        return {
            "level": "action",
            "label": "Actie nodig",
            "message": f"Het huidige plan toont vanaf {year} een tekort.",
        }
    if end_balance < buffer_goal:
        return {
            "level": "attention",
            "label": "Aandacht",
            "message": "Het inkomen blijft op peil, maar de eindbuffer is lager dan je doel.",
        }
    return {
        "level": "good",
        "label": "Op koers",
        "message": "Het berekende inkomen blijft op peil en de eindbuffer blijft behouden.",
    }


def daily_insights(
    result: object,
    settings: Mapping[str, object],
    *,
    limit: int = 3,
) -> list[CockpitInsight]:
    """Bepaal dagelijkse inzichten uitsluitend uit centrale rekenresultaten."""
    insights: list[CockpitInsight] = []
    health = result.projection_health

    if not bool(health["funded"]):
        year = int(health["first_shortfall_year"])
        coverage = float(health["minimum_coverage_pct"])
        insights.append(
            CockpitInsight(
                100,
                "error",
                f"Inkomensplan vraagt aandacht vanaf {year}",
                f"De laagste dekking is {coverage:.1f}% van het gewenste inkomen.",
                "Netto maandinkomen",
            )
        )

    cash_goal = float(settings.get("sale_net_cash_goal", 0) or 0)
    net_cash = float(result.sale["net_cash"])
    if cash_goal > 0 and net_cash < cash_goal:
        insights.append(
            CockpitInsight(
                90,
                "warning",
                "Verkoopscenario onder netto-cashdoel",
                f"Het verschil met je doel is € {cash_goal - net_cash:,.0f}.",
                "Project Vrijheid",
            )
        )

    buffer_goal = float(settings.get("safety_buffer", 0) or 0)
    end_balance = float(health["end_balance"])
    if bool(health["funded"]) and buffer_goal > 0 and end_balance < buffer_goal:
        insights.append(
            CockpitInsight(
                80,
                "warning",
                "Eindbuffer lager dan je ingestelde buffer",
                f"In 2047 resteert naar verwachting € {end_balance:,.0f}.",
                "Plancontrole",
            )
        )

    investment_total = float(result.etf["value"]) + float(result.bitcoin_value)
    if investment_total > 0:
        bitcoin_share = float(result.bitcoin_value) / investment_total * 100
        if bitcoin_share > 20:
            insights.append(
                CockpitInsight(
                    60,
                    "info",
                    "Bitcoin is een groot deel van je beleggingen",
                    f"Bitcoin vormt nu {bitcoin_share:.1f}% van ETF en Bitcoin samen.",
                    "Bitcoin-portefeuille",
                )
            )

    required = {
        "birth_date": "geboortedatum",
        "aow_start_date": "AOW-datum",
        "own_pension_start_date": "pensioendatum",
        "annuity_start_date": "lijfrentedatum",
    }
    missing = [label for key, label in required.items() if not settings.get(key)]
    if missing:
        insights.append(
            CockpitInsight(
                50,
                "info",
                "Persoonlijke aannames zijn nog niet compleet",
                "Controleer: " + ", ".join(missing) + ".",
                "Persoonlijke waarheid",
            )
        )

    if not insights:
        insights.append(
            CockpitInsight(
                10,
                "success",
                "Geen bijzonderheden gevonden",
                "Je centrale berekeningen liggen op basis van de huidige aannames op koers.",
                "Persoonlijke waarheid",
            )
        )

    return sorted(insights, key=lambda item: item.priority, reverse=True)[:limit]
