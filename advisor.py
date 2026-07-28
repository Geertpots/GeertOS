"""Veilige, uitlegbare financiële vraagbeantwoording voor GeertOS."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Mapping

from calculations import money, monte_carlo_income_plan


@dataclass(frozen=True)
class AdvisorAnswer:
    """Een adviserend antwoord dat nooit zelfstandig gegevens wijzigt."""

    title: str
    message: str
    level: str
    details: tuple[str, ...]
    destination: str


def _amounts(question: str) -> list[float]:
    """Lees Nederlandse bedragen, zoals € 1.575.000 of 500, uit een vraag."""
    matches = re.findall(r"(?:€\s*)?(\d[\d.]*(?:,\d{1,2})?)", question)
    values: list[float] = []
    for raw in matches:
        normalized = raw.replace(".", "").replace(",", ".")
        try:
            values.append(float(normalized))
        except ValueError:
            continue
    return values


def _percentage(question: str) -> float | None:
    match = re.search(r"(\d+(?:[.,]\d+)?)\s*%", question)
    if not match:
        return None
    return float(match.group(1).replace(",", "."))


def _decision_answer(
    result: object,
    settings: Mapping[str, object],
    *,
    one_time_cost: float = 0.0,
    extra_monthly: float = 0.0,
) -> AdvisorAnswer:
    summary, _ = monte_carlo_income_plan(
        result.projection,
        starting_capital=result.planned_etf_start,
        expected_return_pct=float(settings.get("etf_return_pct", 4) or 4),
        volatility_pct=12.0,
        simulations=2000,
        one_time_cost=one_time_cost,
        extra_monthly_spending=extra_monthly,
        inflation_pct=float(settings.get("inflation_pct", 2.5) or 2.5),
        seed=42,
    )
    probability = float(summary["success_probability"])
    if probability >= 85:
        level, verdict = "success", "past binnen het huidige plan"
    elif probability >= 65:
        level, verdict = "warning", "lijkt haalbaar, maar verdient aandacht"
    else:
        level, verdict = "error", "brengt het huidige plan duidelijk onder druk"
    decision = (
        f"Een eenmalige uitgave van {money(one_time_cost)}"
        if one_time_cost
        else f"Maandelijks {money(extra_monthly)} extra besteden"
    )
    return AdvisorAnswer(
        "Gevolg voor je plan",
        f"{decision} {verdict}.",
        level,
        (
            f"Kans op volledige dekking in deze simulatie: {probability:.1f}%.",
            f"Mediaan eindvermogen: {money(float(summary['median_end_balance']))}.",
            "Dit is een scenario op basis van aannames, geen garantie.",
        ),
        "Beslislab",
    )


def answer_question(
    question: str,
    engine: object,
    settings: Mapping[str, object],
) -> AdvisorAnswer:
    """Beantwoord herkenbare financiële vragen via de centrale rekenmotor."""
    text = " ".join(question.lower().split())
    amounts = _amounts(question)
    baseline = engine.evaluate()

    if ("pand" in text or "verkoop" in text) and amounts:
        price = max(amounts)
        scenario = engine.evaluate({"sale_property_price": price})
        difference = scenario.sale["net_cash"] - baseline.sale["net_cash"]
        direction = "meer" if difference >= 0 else "minder"
        return AdvisorAnswer(
            "Verkoopscenario POTZ WONEN",
            f"Bij een verkoopprijs van {money(price)} resteert naar verwachting "
            f"{money(scenario.sale['net_cash'])} netto cash.",
            "success" if difference >= 0 else "warning",
            (
                f"Dat is {money(abs(difference))} {direction} dan je huidige scenario.",
                f"Netto vermogen na verkoop: {money(scenario.post_sale_net_worth)}.",
                f"Verwacht ETF-restvermogen in 2047: "
                f"{money(float(scenario.projection_health['end_balance']))}.",
            ),
            "Project Vrijheid",
        )

    bitcoin_down = "daal" in text or "lager" in text or "zakt" in text
    bitcoin_up = (
        "stijg" in text
        or "hoger" in text
        or "omhoog" in text
        or "toeneemt" in text
    )
    if "bitcoin" in text and (bitcoin_down or bitcoin_up):
        percentage = _percentage(question)
        if percentage is None:
            return AdvisorAnswer(
                "Bitcoin-scenario",
                "Noem ook het percentage van de verandering, bijvoorbeeld 20%.",
                "info",
                (),
                "Bitcoin-portefeuille",
            )
        factor = 1 + percentage / 100 if bitcoin_up else max(
            0.0, 1 - percentage / 100
        )
        new_value = baseline.bitcoin_value * factor
        difference = new_value - baseline.bitcoin_value
        percentage_label = f"{percentage:.1f}".replace(".", ",")
        movement = "stijging" if bitcoin_up else "daling"
        impact = "plus" if difference >= 0 else "min"
        return AdvisorAnswer(
            "Bitcoin-scenario",
            f"Na een {movement} van {percentage_label}% is je Bitcoin naar schatting "
            f"{money(new_value)} waard.",
            "success" if bitcoin_up else "warning",
            (
                f"Waardeverandering: {impact} {money(abs(difference))}.",
                f"Effect op het huidige netto vermogen: {impact} "
                f"{money(abs(difference))}.",
                "De pensioenprojectie gebruikt Bitcoin niet als gegarandeerde financieringsbron.",
            ),
            "Bitcoin-portefeuille",
        )

    if ("extra" in text or "meer" in text) and (
        "maand" in text or "opnemen" in text or "besteden" in text
    ) and amounts:
        return _decision_answer(
            baseline, settings, extra_monthly=max(amounts)
        )

    if any(word in text for word in ("camper", "auto", "aankoop", "kopen")) and amounts:
        return _decision_answer(
            baseline, settings, one_time_cost=max(amounts)
        )

    if "financieel onafhankelijk" in text or "financiële vrijheid" in text:
        health = baseline.projection_health
        if bool(health["funded"]):
            return AdvisorAnswer(
                "Financiële vrijheid",
                "Binnen de huidige aannames is het gewenste inkomen tot en met "
                f"{int(baseline.projection.iloc[-1]['year'])} volledig gedekt.",
                "success",
                (
                    f"Vrijheidsstatus: {baseline.freedom_score}%.",
                    f"Verwacht eindvermogen: {money(float(health['end_balance']))}.",
                    "Controleer grote beslissingen altijd opnieuw in het Beslislab.",
                ),
                "Vrijheidstijdlijn",
            )
        return AdvisorAnswer(
            "Financiële vrijheid",
            f"Het huidige plan toont vanaf {int(health['first_shortfall_year'])} "
            "een tekort.",
            "error",
            (
                f"Laagste inkomensdekking: {float(health['minimum_coverage_pct']):.1f}%.",
                "Bekijk de tijdlijn om het omslagpunt te onderzoeken.",
            ),
            "Vrijheidstijdlijn",
        )

    return AdvisorAnswer(
        "Ik heb meer richting nodig",
        "Deze veilige eerste adviseur herkent vragen over verkoopprijs, extra "
        "maanduitgaven, grote aankopen, Bitcoin-dalingen en financiële vrijheid.",
        "info",
        (
            "Probeer bijvoorbeeld: Wat gebeurt er als het pand € 1.575.000 oplevert?",
            "Of: Kan ik veilig € 80.000 aan een camper besteden?",
        ),
        "Vandaag",
    )
