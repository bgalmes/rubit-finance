"""Fixed-rate mortgage maths using the French amortization system.

Pure Python: no framework imports, so it can be tested in isolation.
All money is handled as ``Decimal``. The payment and each period's interest are
rounded to cents (half-up); the last period absorbs any leftover cents so the
outstanding balance ends at exactly 0.00.
"""

from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from enum import StrEnum

ZERO = Decimal(0)
CENT = Decimal("0.01")
HUNDRED = Decimal(100)

MIN_YEARS = 1
MAX_YEARS = 50
MAX_TIN = HUNDRED


class MortgageValidationError(ValueError):
    """Raised when mortgage conditions break a validation rule."""

    def __init__(self, field_name: str, message: str) -> None:
        super().__init__(f"{field_name}: {message}")
        self.field_name = field_name
        self.message = message


class PaymentFrequency(StrEnum):
    MONTHLY = "monthly"
    ANNUAL = "annual"

    @property
    def payments_per_year(self) -> int:
        return 12 if self is PaymentFrequency.MONTHLY else 1


def to_cents(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


@dataclass(frozen=True, slots=True)
class PurchaseInfo:
    """Mode A: the loan is derived from the purchase."""

    price: Decimal
    savings: Decimal = ZERO
    expenses: Decimal = ZERO

    def __post_init__(self) -> None:
        if self.price <= ZERO:
            raise MortgageValidationError("purchase_price", "must be greater than 0")
        if self.savings < ZERO:
            raise MortgageValidationError("initial_savings", "must be 0 or greater")
        if self.expenses < ZERO:
            raise MortgageValidationError("initial_expenses", "must be 0 or greater")
        if self.savings >= self.price + self.expenses:
            raise MortgageValidationError(
                "initial_savings",
                "must be less than purchase price + initial expenses",
            )

    @property
    def down_payment(self) -> Decimal:
        """Savings pay the expenses first; the rest goes towards the price."""
        return self.savings - self.expenses

    @property
    def loan_amount(self) -> Decimal:
        return self.price + self.expenses - self.savings


@dataclass(frozen=True, slots=True)
class MortgageConditions:
    """Inputs that define a mortgage: either ``purchase`` (mode A) or ``loan`` (mode B)."""

    tin: Decimal
    years: int
    frequency: PaymentFrequency = PaymentFrequency.MONTHLY
    purchase: PurchaseInfo | None = None
    loan: Decimal | None = None

    def __post_init__(self) -> None:
        if not ZERO <= self.tin <= MAX_TIN:
            raise MortgageValidationError("tin", f"must be between 0 and {MAX_TIN}")
        if not MIN_YEARS <= self.years <= MAX_YEARS:
            raise MortgageValidationError("years", f"must be between {MIN_YEARS} and {MAX_YEARS}")
        if (self.purchase is None) == (self.loan is None):
            raise MortgageValidationError(
                "mode", "provide either purchase information or a loan amount"
            )
        if self.loan is not None and self.loan <= ZERO:
            raise MortgageValidationError("loan_amount", "must be greater than 0")

    @property
    def loan_amount(self) -> Decimal:
        if self.purchase is not None:
            return to_cents(self.purchase.loan_amount)
        assert self.loan is not None
        return to_cents(self.loan)

    @property
    def down_payment(self) -> Decimal | None:
        return None if self.purchase is None else self.purchase.down_payment

    @property
    def purchase_percentage(self) -> Decimal | None:
        """Loan amount as a percentage of the purchase price (e.g. ``80.00``)."""
        if self.purchase is None:
            return None
        return to_cents(self.loan_amount / self.purchase.price * HUNDRED)

    @property
    def number_of_payments(self) -> int:
        return self.years * self.frequency.payments_per_year

    @property
    def periodic_rate(self) -> Decimal:
        return self.tin / HUNDRED / self.frequency.payments_per_year


@dataclass(frozen=True, slots=True)
class AmortizationRow:
    period: int
    payment: Decimal
    interest: Decimal
    principal: Decimal
    balance: Decimal
    amortized: Decimal


@dataclass(frozen=True, slots=True)
class MortgageSummary:
    loan_amount: Decimal
    down_payment: Decimal | None
    purchase_percentage: Decimal | None
    payment: Decimal
    total_interest: Decimal
    total_paid: Decimal
    schedule: tuple[AmortizationRow, ...] = field(repr=False)


def periodic_payment(loan: Decimal, rate: Decimal, periods: int) -> Decimal:
    """French system payment: ``P = L·r / (1 − (1 + r)^−n)``, or ``L / n`` when ``r = 0``."""
    if rate == ZERO:
        return to_cents(loan / periods)
    return to_cents(loan * rate / (1 - (1 + rate) ** -periods))


def amortization_schedule(conditions: MortgageConditions) -> tuple[AmortizationRow, ...]:
    loan = conditions.loan_amount
    rate = conditions.periodic_rate
    periods = conditions.number_of_payments
    payment = periodic_payment(loan, rate, periods)

    rows: list[AmortizationRow] = []
    balance = loan
    amortized = ZERO
    for period in range(1, periods + 1):
        interest = to_cents(balance * rate)
        # The last period pays off the remaining balance. Before that, clamp so
        # rounding can never overshoot the balance on tiny loans.
        is_last = period == periods
        principal = balance if is_last else min(max(payment - interest, ZERO), balance)
        balance -= principal
        amortized += principal
        rows.append(
            AmortizationRow(
                period=period,
                payment=interest + principal,
                interest=interest,
                principal=principal,
                balance=balance,
                amortized=amortized,
            )
        )
    return tuple(rows)


def summarize(conditions: MortgageConditions) -> MortgageSummary:
    loan = conditions.loan_amount
    schedule = amortization_schedule(conditions)
    total_interest = sum((row.interest for row in schedule), ZERO)
    return MortgageSummary(
        loan_amount=loan,
        down_payment=conditions.down_payment,
        purchase_percentage=conditions.purchase_percentage,
        payment=periodic_payment(loan, conditions.periodic_rate, conditions.number_of_payments),
        total_interest=total_interest,
        total_paid=loan + total_interest,
        schedule=schedule,
    )
