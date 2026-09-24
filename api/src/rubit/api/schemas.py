"""HTTP request/response schemas. Decimals are serialized as JSON strings."""

from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from rubit.domain import PaymentFrequency
from rubit.domain.mortgage import MAX_TIN, MAX_YEARS, MIN_YEARS
from rubit.persistence import MortgageMode

Money = Annotated[Decimal, Field(max_digits=14, decimal_places=2)]


class MortgageBaseIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, max_length=100)
    tin: Annotated[Decimal, Field(ge=0, le=MAX_TIN, max_digits=7, decimal_places=4)]
    years: int = Field(ge=MIN_YEARS, le=MAX_YEARS)
    frequency: PaymentFrequency = PaymentFrequency.MONTHLY

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


class AmortizationRowOut(BaseModel):
    period: int
    payment: Decimal
    interest: Decimal
    principal: Decimal
    balance: Decimal
    amortized: Decimal


class MortgageOut(BaseModel):
    id: int
    name: str
    mode: MortgageMode
    tin: Decimal
    years: int
    frequency: PaymentFrequency
    purchase_price: Decimal | None
    initial_savings: Decimal | None
    initial_expenses: Decimal | None
    down_payment: Decimal | None
    loan_amount: Decimal
    purchase_percentage: Decimal | None
    payment: Decimal
    total_interest: Decimal
    total_paid: Decimal


class MortgageDetailOut(MortgageOut):
    schedule: list[AmortizationRowOut]


class ComparisonOut(BaseModel):
    mortgages: list[MortgageOut]
