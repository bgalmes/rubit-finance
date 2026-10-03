"""Fixed-rate mortgage maths using the French amortization system.

Pure Python: no framework imports, so it can be tested in isolation.
All money is handled as ``Decimal``. The payment and each period's interest are
rounded to cents (half-up); the last period absorbs any leftover cents so the
outstanding balance ends at exactly 0.00.

Early amortizations are applied right after the regular payment of their period.
"""

from collections.abc import Iterable
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from enum import StrEnum
from math import ceil

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


class AmortizationType(StrEnum):
    CAPITAL = "capital"
    """Keeps the term; the payment is recalculated lower."""
    PERIODS = "periods"
    """Keeps the payment; the term gets shorter."""


@dataclass(frozen=True, slots=True)
class EarlyAmortization:
    """An early repayment made after the regular payment of ``period``.

    It is given either as an ``amount``, or (``periods`` type only) as the number of
    ``periods`` to cut from the term, in which case the amount is derived.
    """

    period: int
    type: AmortizationType
    amount: Decimal | None = None
    periods: int | None = None

    def __post_init__(self) -> None:
        if self.period < 1:
            raise MortgageValidationError("period", "must be 1 or greater")
        if (self.amount is None) == (self.periods is None):
            raise MortgageValidationError(
                "amount", "provide either an amount or a number of periods"
            )
        if self.type is AmortizationType.CAPITAL and self.periods is not None:
            raise MortgageValidationError(
                "periods", "only periods amortizations take a number of periods"
            )
        if self.amount is not None and self.amount <= ZERO:
            raise MortgageValidationError("amount", "must be greater than 0")
        if self.periods is not None and self.periods < 1:
            raise MortgageValidationError("periods", "must be 1 or greater")


@dataclass(frozen=True, slots=True)
class AmortizationRow:
    period: int
    year: int
    payment: Decimal
    interest: Decimal
    principal: Decimal
    early_amortization: Decimal
    balance: Decimal
    amortized: Decimal


@dataclass(frozen=True, slots=True)
class MortgageSummary:
    loan_amount: Decimal
    down_payment: Decimal | None
    purchase_percentage: Decimal | None
    payment: Decimal
    """The initial payment per period."""
    current_payment: Decimal
    """The payment per period after the last early amortization."""
    total_interest: Decimal
    total_paid: Decimal
    total_early_amortized: Decimal
    number_of_payments: int
    interest_saved: Decimal
    """Interest saved by the early amortizations."""
    payments_saved: int
    """Periods cut from the term by the early amortizations."""
    schedule: tuple[AmortizationRow, ...] = field(repr=False)


def periodic_payment(loan: Decimal, rate: Decimal, periods: int) -> Decimal:
    """French system payment: ``P = L·r / (1 − (1 + r)^−n)``, or ``L / n`` when ``r = 0``."""
    if rate == ZERO:
        return to_cents(loan / periods)
    return to_cents(loan * rate / (1 - (1 + rate) ** -periods))


def present_value(payment: Decimal, rate: Decimal, periods: int) -> Decimal:
    """Balance that ``periods`` payments of ``payment`` repay (inverse of ``periodic_payment``)."""
    if rate == ZERO:
        return to_cents(payment * periods)
    return to_cents(payment * (1 - (1 + rate) ** -periods) / rate)


def periods_to_repay(balance: Decimal, payment: Decimal, rate: Decimal) -> int:
    """Payments of ``payment`` needed to repay ``balance``; the last one may be smaller."""
    if rate == ZERO:
        return ceil(balance / payment)
    return ceil(-(1 - balance * rate / payment).ln() / (1 + rate).ln())


def _by_period(amortizations: Iterable[EarlyAmortization]) -> dict[int, EarlyAmortization]:
    by_period: dict[int, EarlyAmortization] = {}
    for amortization in amortizations:
        if amortization.period in by_period:
            raise MortgageValidationError(
                "period", f"period {amortization.period}: only one amortization per period"
            )
        by_period[amortization.period] = amortization
    return by_period


def _build_schedule(
    conditions: MortgageConditions, amortizations: Iterable[EarlyAmortization]
) -> tuple[tuple[AmortizationRow, ...], Decimal]:
    """The schedule and the payment per period in force at its end."""
    pending = _by_period(amortizations)
    loan = conditions.loan_amount
    rate = conditions.periodic_rate
    per_year = conditions.frequency.payments_per_year
    last_period = conditions.number_of_payments
    payment = periodic_payment(loan, rate, last_period)

    rows: list[AmortizationRow] = []
    balance = loan
    amortized = ZERO
    period = 0
    while balance > ZERO:
        period += 1
        interest = to_cents(balance * rate)
        # The last period pays off the remaining balance. Before that, clamp so
        # rounding can never overshoot the balance on tiny loans.
        is_last = period == last_period
        principal = balance if is_last else min(max(payment - interest, ZERO), balance)
        balance -= principal
        amortized += principal

        early = to_cents(ZERO)
        amortization = pending.pop(period, None)
        if amortization is not None:
            if balance == ZERO:
                raise MortgageValidationError(
                    "period", f"period {period}: the loan is already paid off"
                )
            remaining = last_period - period
            if amortization.periods is not None:
                if amortization.periods > remaining:
                    raise MortgageValidationError(
                        "periods", f"period {period}: must be at most {remaining}, the periods left"
                    )
                last_period -= amortization.periods
                early = balance - present_value(payment, rate, last_period - period)
            else:
                assert amortization.amount is not None
                early = to_cents(amortization.amount)
                if early > balance:
                    raise MortgageValidationError(
                        "amount",
                        f"period {period}: must not exceed the outstanding balance ({balance})",
                    )
            balance -= early
            amortized += early
            if balance == ZERO:
                payment = to_cents(ZERO)  # cancelled: nothing more to pay
            elif amortization.type is AmortizationType.CAPITAL:
                payment = periodic_payment(balance, rate, remaining)
            elif amortization.amount is not None and payment > ZERO:
                last_period = period + min(periods_to_repay(balance, payment, rate), remaining)

        rows.append(
            AmortizationRow(
                period=period,
                year=(period - 1) // per_year + 1,
                payment=interest + principal,
                interest=interest,
                principal=principal,
                early_amortization=early,
                balance=balance,
                amortized=amortized,
            )
        )

    if pending:
        late = min(pending)
        raise MortgageValidationError("period", f"period {late}: the loan is already paid off")
    return tuple(rows), payment


def amortization_schedule(
    conditions: MortgageConditions, amortizations: Iterable[EarlyAmortization] = ()
) -> tuple[AmortizationRow, ...]:
    """The French schedule, with any early amortizations applied.

    Raises ``MortgageValidationError`` when an amortization doesn't fit the schedule.
    """
    return _build_schedule(conditions, amortizations)[0]


def _total_interest(schedule: Iterable[AmortizationRow]) -> Decimal:
    return sum((row.interest for row in schedule), ZERO)


def summarize(
    conditions: MortgageConditions, amortizations: Iterable[EarlyAmortization] = ()
) -> MortgageSummary:
    loan = conditions.loan_amount
    schedule, current_payment = _build_schedule(conditions, amortizations)
    total_interest = _total_interest(schedule)
    baseline = amortization_schedule(conditions)
    return MortgageSummary(
        loan_amount=loan,
        down_payment=conditions.down_payment,
        purchase_percentage=conditions.purchase_percentage,
        payment=periodic_payment(loan, conditions.periodic_rate, conditions.number_of_payments),
        current_payment=current_payment,
        total_interest=total_interest,
        total_paid=loan + total_interest,
        total_early_amortized=sum((row.early_amortization for row in schedule), ZERO),
        number_of_payments=len(schedule),
        interest_saved=_total_interest(baseline) - total_interest,
        payments_saved=len(baseline) - len(schedule),
        schedule=schedule,
    )
