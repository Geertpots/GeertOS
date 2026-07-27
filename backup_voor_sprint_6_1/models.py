from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from math import isfinite
from typing import Optional


def _utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


def _validate_non_negative_amount(value: float, field_name: str) -> None:
    """Validate that a monetary amount is finite and not negative."""
    if not isfinite(value):
        raise ValueError(f"{field_name} moet een geldig getal zijn.")
    if value < 0:
        raise ValueError(f"{field_name} mag niet negatief zijn.")


def _validate_percentage(value: float, field_name: str) -> None:
    """Validate a percentage expressed as a number between 0 and 100."""
    if not isfinite(value):
        raise ValueError(f"{field_name} moet een geldig getal zijn.")
    if not 0 <= value <= 100:
        raise ValueError(f"{field_name} moet tussen 0 en 100 liggen.")


class AssetType(str, Enum):
    PROPERTY = "property"
    INVENTORY = "inventory"
    ETF = "etf"
    BITCOIN = "bitcoin"
    CASH = "cash"
    PENSION = "pension"
    ANNUITY = "annuity"
    OTHER = "other"


class LiabilityType(str, Enum):
    MORTGAGE = "mortgage"
    BUSINESS_LOAN = "business_loan"
    PERSONAL_LOAN = "personal_loan"
    TAX = "tax"
    OTHER = "other"


@dataclass(slots=True)
class Asset:
    name: str
    asset_type: AssetType
    amount: float
    notes: str = ""
    id: Optional[int] = None
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)

    def __post_init__(self) -> None:
        self.name = self.name.strip()
        self.notes = self.notes.strip()

        if not self.name:
            raise ValueError("Naam van het bezit is verplicht.")

        _validate_non_negative_amount(self.amount, "Bedrag")


@dataclass(slots=True)
class Liability:
    name: str
    liability_type: LiabilityType
    amount: float
    notes: str = ""
    id: Optional[int] = None
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)

    def __post_init__(self) -> None:
        self.name = self.name.strip()
        self.notes = self.notes.strip()

        if not self.name:
            raise ValueError("Naam van de schuld is verplicht.")

        _validate_non_negative_amount(self.amount, "Bedrag")


@dataclass(slots=True)
class Settings:
    target_monthly_income: float
    inflation: float
    etf_return: float
    safety_buffer: float
    calculation_end_year: int
    id: Optional[int] = None
    updated_at: datetime = field(default_factory=_utc_now)

    def __post_init__(self) -> None:
        _validate_non_negative_amount(
            self.target_monthly_income,
            "Gewenst netto maandinkomen",
        )
        _validate_percentage(self.inflation, "Inflatie")
        _validate_percentage(self.etf_return, "ETF-rendement")
        _validate_non_negative_amount(self.safety_buffer, "Veiligheidsbuffer")

        current_year = datetime.now().year
        if self.calculation_end_year < current_year:
            raise ValueError(
                "Het eindjaar van de berekening mag niet in het verleden liggen."
            )
        if self.calculation_end_year > current_year + 100:
            raise ValueError("Het eindjaar ligt onrealistisch ver in de toekomst.")


@dataclass(frozen=True, slots=True)
class BalanceSheet:
    total_assets: float
    total_liabilities: float

    def __post_init__(self) -> None:
        _validate_non_negative_amount(self.total_assets, "Totale bezittingen")
        _validate_non_negative_amount(self.total_liabilities, "Totale schulden")

    @property
    def net_worth(self) -> float:
        return self.total_assets - self.total_liabilities


@dataclass(slots=True)
class FreedomScenario:
    expected_property_sale: float
    expected_inventory_sale: float
    mortgage: float
    business_credit: float
    other_loans: float
    tax_reserve: float
    annuity_deposit: float
    brokerage_costs: float = 0.0
    other_sale_costs: float = 0.0
    name: str = "Verwacht"
    id: Optional[int] = None
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)

    def __post_init__(self) -> None:
        self.name = self.name.strip()

        if not self.name:
            raise ValueError("Naam van het scenario is verplicht.")

        monetary_fields = {
            "Verwachte verkoopprijs pand": self.expected_property_sale,
            "Verwachte verkoopprijs voorraad": self.expected_inventory_sale,
            "Hypotheek": self.mortgage,
            "Bedrijfskrediet": self.business_credit,
            "Overige leningen": self.other_loans,
            "Belastingreservering": self.tax_reserve,
            "Lijfrentestorting": self.annuity_deposit,
            "Makelaarskosten": self.brokerage_costs,
            "Overige verkoopkosten": self.other_sale_costs,
        }

        for field_name, value in monetary_fields.items():
            _validate_non_negative_amount(value, field_name)

    @property
    def total_sale(self) -> float:
        return self.expected_property_sale + self.expected_inventory_sale

    @property
    def total_debt(self) -> float:
        return self.mortgage + self.business_credit + self.other_loans

    @property
    def total_sale_costs(self) -> float:
        return self.brokerage_costs + self.other_sale_costs

    @property
    def net_cash_before_tax_and_annuity(self) -> float:
        return self.total_sale - self.total_debt - self.total_sale_costs

    @property
    def net_cash(self) -> float:
        return (
            self.net_cash_before_tax_and_annuity
            - self.tax_reserve
            - self.annuity_deposit
        )
