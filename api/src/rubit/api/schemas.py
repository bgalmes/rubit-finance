"""HTTP request/response schemas. Decimals are serialized as JSON strings."""

import datetime as dt
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from rubit.domain import AmortizationType, PaymentFrequency
from rubit.domain.mortgage import MAX_TIN, MAX_YEARS, MIN_YEARS
from rubit.persistence import MortgageMode

Money = Annotated[Decimal, Field(max_digits=14, decimal_places=2)]


class MortgageBaseIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, max_length=100)
    tin: Annotated[Decimal, Field(ge=0, le=MAX_TIN, max_digits=7, decimal_places=4)]
    years: int = Field(ge=MIN_YEARS, le=MAX_YEARS)
    frequency: PaymentFrequency = PaymentFrequency.MONTHLY
    start_date: dt.date | None = None
    """The signing date; the rest of its month pays interest only."""

    @field_validator("name")
    @classmethod
    def blank_name_is_none(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None


class PurchaseMortgageIn(MortgageBaseIn):
    mode: Literal[MortgageMode.PURCHASE]
    purchase_price: Annotated[Money, Field(gt=0)]
    initial_savings: Annotated[Money, Field(ge=0)] = Decimal(0)
    initial_expenses: Annotated[Money, Field(ge=0)] = Decimal(0)


class LoanMortgageIn(MortgageBaseIn):
    mode: Literal[MortgageMode.LOAN]
    loan_amount: Annotated[Money, Field(gt=0)]


MortgageIn = Annotated[PurchaseMortgageIn | LoanMortgageIn, Field(discriminator="mode")]


class AmortizationIn(BaseModel):
    """An early amortization: an ``amount``, or (``periods`` type) the ``periods`` to cut."""

    model_config = ConfigDict(extra="forbid")

    type: AmortizationType
    amount: Annotated[Money, Field(gt=0)] | None = None
    periods: int | None = Field(default=None, ge=1)


class AmortizationOut(BaseModel):
    period: int
    type: AmortizationType
    amount: Decimal | None
    periods: int | None
    applied_amount: Decimal
    """The amount actually repaid (derived when given as a number of periods)."""


class AmortizationRowOut(BaseModel):
    period: int
    year: int
    payment: Decimal
    interest: Decimal
    principal: Decimal
    early_amortization: Decimal
    balance: Decimal
    amortized: Decimal
    date: dt.date | None
    """First day of the payment month, when the mortgage has a signing date."""


class MortgageOut(BaseModel):
    id: int
    name: str
    mode: MortgageMode
    tin: Decimal
    years: int
    frequency: PaymentFrequency
    start_date: dt.date | None
    end_date: dt.date | None
    """Month of the last payment, when the mortgage has a signing date."""
    purchase_price: Decimal | None
    initial_savings: Decimal | None
    initial_expenses: Decimal | None
    down_payment: Decimal | None
    loan_amount: Decimal
    purchase_percentage: Decimal | None
    payment: Decimal
    current_payment: Decimal
    total_interest: Decimal
    total_paid: Decimal
    total_early_amortized: Decimal
    number_of_payments: int
    interest_saved: Decimal
    payments_saved: int


class MortgageDetailOut(MortgageOut):
    amortizations: list[AmortizationOut]
    schedule: list[AmortizationRowOut]


class ComparisonOut(BaseModel):
    mortgages: list[MortgageOut]
