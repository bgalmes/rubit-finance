"""Database models. Only the mortgage inputs are stored; derived data is computed on request."""

from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import Dialect, String
from sqlalchemy.types import TypeDecorator
from sqlmodel import Field, SQLModel

from rubit.domain import MortgageConditions, PaymentFrequency, PurchaseInfo


class DecimalString(TypeDecorator[Decimal]):
    """Stores ``Decimal`` as TEXT so SQLite never turns money into floats."""

    impl = String
    cache_ok = True

    def process_bind_param(self, value: Decimal | None, dialect: Dialect) -> str | None:
        return None if value is None else str(value)

    def process_result_value(self, value: str | None, dialect: Dialect) -> Decimal | None:
        return None if value is None else Decimal(value)


class MortgageMode(StrEnum):
    PURCHASE = "purchase"
    LOAN = "loan"


class MortgageRecord(SQLModel, table=True):
    __tablename__ = "mortgages"  # pyright: ignore[reportAssignmentType, reportIncompatibleVariableOverride]

    id: int | None = Field(default=None, primary_key=True)
    name: str
    mode: MortgageMode
    tin: Decimal = Field(sa_type=DecimalString)
    years: int
    frequency: PaymentFrequency
    purchase_price: Decimal | None = Field(default=None, sa_type=DecimalString)
    initial_savings: Decimal | None = Field(default=None, sa_type=DecimalString)
    initial_expenses: Decimal | None = Field(default=None, sa_type=DecimalString)
    loan_amount: Decimal | None = Field(default=None, sa_type=DecimalString)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def to_conditions(self) -> MortgageConditions:
        purchase = None
        if self.mode is MortgageMode.PURCHASE:
            assert self.purchase_price is not None
            purchase = PurchaseInfo(
                price=self.purchase_price,
                savings=self.initial_savings or Decimal(0),
                expenses=self.initial_expenses or Decimal(0),
            )
        return MortgageConditions(
            tin=self.tin,
            years=self.years,
            frequency=self.frequency,
            purchase=purchase,
            loan=self.loan_amount if self.mode is MortgageMode.LOAN else None,
        )
