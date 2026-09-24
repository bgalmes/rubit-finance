from decimal import Decimal

import pytest

from rubit.domain import (
    MortgageConditions,
    MortgageValidationError,
    PaymentFrequency,
    PurchaseInfo,
    amortization_schedule,
    periodic_payment,
    summarize,
)

D = Decimal


def loan_mortgage(
    loan: str = "200000",
    tin: str = "3",
    years: int = 30,
    frequency: PaymentFrequency = PaymentFrequency.MONTHLY,
) -> MortgageConditions:
    return MortgageConditions(tin=D(tin), years=years, frequency=frequency, loan=D(loan))


class TestReferenceExample:
    """PLAN.md: L = 200,000 €, TIN 3%, 30 years, monthly → P ≈ 843.21 €."""

    def test_payment(self) -> None:
        assert summarize(loan_mortgage()).payment == D("843.21")

    def test_schedule_shape(self) -> None:
        schedule = amortization_schedule(loan_mortgage())
        assert len(schedule) == 360
        assert [row.period for row in schedule] == list(range(1, 361))

    def test_first_row(self) -> None:
        first = amortization_schedule(loan_mortgage())[0]
        assert first.interest == D("500.00")
        assert first.principal == D("343.21")
        assert first.payment == D("843.21")
        assert first.balance == D("199656.79")
        assert first.amortized == D("343.21")

    def test_last_row_closes_balance(self) -> None:
        schedule = amortization_schedule(loan_mortgage())
        previous, last = schedule[-2], schedule[-1]
        assert last.balance == D("0.00")
        assert last.amortized == D("200000.00")
        # The last period pays off whatever balance is left.
        assert last.principal == previous.balance
        assert last.payment == last.interest + previous.balance
        # Accumulated cent rounding over 360 periods stays small.
        assert abs(last.payment - D("843.21")) < D("2.00")

    def test_totals_are_consistent(self) -> None:
        summary = summarize(loan_mortgage())
        schedule = summary.schedule
        assert sum(row.principal for row in schedule) == D("200000.00")
        assert summary.total_interest == sum(row.interest for row in schedule)
        assert summary.total_paid == summary.loan_amount + summary.total_interest
        assert summary.total_paid == sum(row.payment for row in schedule)

    def test_loan_mode_has_no_purchase_data(self) -> None:
        summary = summarize(loan_mortgage())
        assert summary.down_payment is None
        assert summary.purchase_percentage is None


class TestPurchaseMode:
    def test_loan_formula(self) -> None:
        purchase = PurchaseInfo(price=D("250000"), savings=D("70000"), expenses=D("20000"))
        conditions = MortgageConditions(tin=D("3"), years=30, purchase=purchase)
        # loan = price + expenses − savings; down payment = savings − expenses
        assert conditions.loan_amount == D("200000.00")
        assert conditions.down_payment == D("50000")
        assert conditions.purchase_percentage == D("80.00")
        assert summarize(conditions).payment == D("843.21")

    def test_defaults(self) -> None:
        purchase = PurchaseInfo(price=D("100000"))
        conditions = MortgageConditions(tin=D("2"), years=10, purchase=purchase)
        assert conditions.loan_amount == D("100000.00")
        assert conditions.down_payment == D("0")
        assert conditions.purchase_percentage == D("100.00")

    def test_expenses_above_savings_are_financed(self) -> None:
        purchase = PurchaseInfo(price=D("100000"), savings=D("5000"), expenses=D("10000"))
        conditions = MortgageConditions(tin=D("2"), years=10, purchase=purchase)
        assert conditions.down_payment == D("-5000")
        assert conditions.purchase_percentage == D("105.00")


class TestSpecialCases:
    def test_zero_interest(self) -> None:
        conditions = loan_mortgage(loan="12000", tin="0", years=1)
        summary = summarize(conditions)
        assert summary.payment == D("1000.00")
        assert summary.total_interest == D("0")
        assert all(row.interest == D("0.00") for row in summary.schedule)
        assert summary.schedule[-1].balance == D("0.00")

    def test_zero_interest_uneven_split(self) -> None:
        summary = summarize(loan_mortgage(loan="1000", tin="0", years=1))
        assert summary.payment == D("83.33")
        assert summary.schedule[-1].payment == D("83.37")
        assert summary.schedule[-1].balance == D("0.00")

    def test_annual_frequency(self) -> None:
        conditions = loan_mortgage(
            loan="100000", tin="5", years=10, frequency=PaymentFrequency.ANNUAL
        )
        assert conditions.number_of_payments == 10
        assert conditions.periodic_rate == D("0.05")
        summary = summarize(conditions)
        assert summary.payment == D("12950.46")
        assert len(summary.schedule) == 10
        assert summary.schedule[-1].balance == D("0.00")

    def test_tiny_loan_never_overshoots(self) -> None:
        schedule = amortization_schedule(loan_mortgage(loan="1", tin="0", years=50))
        assert all(row.balance >= D("0") for row in schedule)
        assert all(row.principal >= D("0") for row in schedule)
        assert schedule[-1].balance == D("0.00")

    def test_periodic_payment_function(self) -> None:
        assert periodic_payment(D("200000"), D("0.0025"), 360) == D("843.21")
        assert periodic_payment(D("600"), D("0"), 6) == D("100.00")

    def test_frequency_payments_per_year(self) -> None:
        assert PaymentFrequency.MONTHLY.payments_per_year == 12
        assert PaymentFrequency.ANNUAL.payments_per_year == 1


class TestValidation:
    @pytest.mark.parametrize("tin", ["0", "100"])
    def test_tin_bounds_accepted(self, tin: str) -> None:
        loan_mortgage(tin=tin)

    @pytest.mark.parametrize("tin", ["-0.01", "100.01"])
    def test_tin_bounds_rejected(self, tin: str) -> None:
        with pytest.raises(MortgageValidationError) as exc:
            loan_mortgage(tin=tin)
        assert exc.value.field_name == "tin"

    @pytest.mark.parametrize("years", [1, 50])
    def test_years_bounds_accepted(self, years: int) -> None:
        loan_mortgage(years=years)

    @pytest.mark.parametrize("years", [0, 51])
    def test_years_bounds_rejected(self, years: int) -> None:
        with pytest.raises(MortgageValidationError) as exc:
            loan_mortgage(years=years)
        assert exc.value.field_name == "years"

    @pytest.mark.parametrize("loan", ["0", "-1"])
    def test_loan_must_be_positive(self, loan: str) -> None:
        with pytest.raises(MortgageValidationError) as exc:
            loan_mortgage(loan=loan)
        assert exc.value.field_name == "loan_amount"

    def test_needs_exactly_one_mode(self) -> None:
        with pytest.raises(MortgageValidationError) as exc:
            MortgageConditions(tin=D("3"), years=30)
        assert exc.value.field_name == "mode"
        with pytest.raises(MortgageValidationError):
            MortgageConditions(
                tin=D("3"), years=30, purchase=PurchaseInfo(price=D("1")), loan=D("1")
            )

    @pytest.mark.parametrize(
        ("kwargs", "field_name"),
        [
            ({"price": D("0")}, "purchase_price"),
            ({"price": D("100"), "savings": D("-1")}, "initial_savings"),
            ({"price": D("100"), "expenses": D("-1")}, "initial_expenses"),
            ({"price": D("100"), "savings": D("110"), "expenses": D("10")}, "initial_savings"),
        ],
    )
    def test_purchase_rules(self, kwargs: dict[str, Decimal], field_name: str) -> None:
        with pytest.raises(MortgageValidationError) as exc:
            PurchaseInfo(**kwargs)
        assert exc.value.field_name == field_name
        assert field_name in str(exc.value)

    def test_savings_just_below_limit(self) -> None:
        purchase = PurchaseInfo(price=D("100"), savings=D("109.99"), expenses=D("10"))
        assert purchase.loan_amount == D("0.01")
