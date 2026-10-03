from datetime import date
from decimal import Decimal

import pytest

from rubit.domain import (
    AmortizationType,
    EarlyAmortization,
    MortgageConditions,
    MortgageValidationError,
    PaymentFrequency,
    PurchaseInfo,
    amortization_schedule,
    periodic_payment,
    periods_to_repay,
    present_value,
    stub_days,
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
        assert [row.year for row in schedule[:13]] == [1] * 12 + [2]
        assert schedule[-1].year == 30
        assert all(row.early_amortization == D("0") for row in schedule)

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
        assert [row.year for row in summary.schedule] == list(range(1, 11))
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


CAPITAL = AmortizationType.CAPITAL
PERIODS = AmortizationType.PERIODS


def capital(period: int, amount: str) -> EarlyAmortization:
    return EarlyAmortization(period=period, type=CAPITAL, amount=D(amount))


def by_amount(period: int, amount: str) -> EarlyAmortization:
    return EarlyAmortization(period=period, type=PERIODS, amount=D(amount))


def by_periods(period: int, periods: int) -> EarlyAmortization:
    return EarlyAmortization(period=period, type=PERIODS, periods=periods)


def assert_consistent(conditions: MortgageConditions, *amortizations: EarlyAmortization) -> None:
    summary = summarize(conditions, amortizations)
    schedule = summary.schedule
    assert schedule[-1].balance == D("0.00")
    assert all(row.balance >= D("0") for row in schedule)
    assert sum(row.principal + row.early_amortization for row in schedule) == summary.loan_amount
    assert schedule[-1].amortized == summary.loan_amount
    assert summary.total_paid == summary.loan_amount + summary.total_interest


class TestNoAmortizations:
    def test_summary_has_no_savings(self) -> None:
        summary = summarize(loan_mortgage())
        assert summary.current_payment == summary.payment
        assert summary.number_of_payments == 360
        assert summary.total_early_amortized == D("0")
        assert summary.interest_saved == D("0")
        assert summary.payments_saved == 0


class TestCapitalAmortization:
    def test_keeps_term_and_lowers_payment(self) -> None:
        summary = summarize(loan_mortgage(), [capital(12, "20000")])
        row = summary.schedule[11]
        assert row.early_amortization == D("20000.00")
        assert row.payment == D("843.21")
        assert row.amortized == summary.schedule[10].amortized + row.principal + D("20000")
        assert summary.schedule[12].payment == D("757.09")
        assert summary.number_of_payments == 360
        assert summary.payments_saved == 0
        assert summary.payment == D("843.21")
        assert summary.current_payment == D("757.09")
        assert summary.total_early_amortized == D("20000.00")
        assert summary.interest_saved > D("0")
        assert_consistent(loan_mortgage(), capital(12, "20000"))

    def test_payment_matches_fresh_loan_over_remaining_term(self) -> None:
        schedule = amortization_schedule(loan_mortgage(), [capital(60, "10000")])
        expected = periodic_payment(schedule[59].balance, D("0.0025"), 300)
        assert schedule[60].payment == expected

    def test_full_cancellation(self) -> None:
        balance = amortization_schedule(loan_mortgage())[11].balance
        summary = summarize(loan_mortgage(), [capital(12, str(balance))])
        assert summary.number_of_payments == 12
        assert summary.payments_saved == 348
        assert summary.schedule[-1].balance == D("0.00")
        assert summary.current_payment == D("0.00")

    def test_zero_interest(self) -> None:
        conditions = loan_mortgage(loan="12000", tin="0", years=1)
        summary = summarize(conditions, [capital(6, "3000")])
        assert summary.schedule[6].payment == D("500.00")
        assert summary.number_of_payments == 12
        assert summary.interest_saved == D("0")
        assert_consistent(conditions, capital(6, "3000"))


class TestPeriodsAmortization:
    def test_by_amount_keeps_payment_and_shortens_term(self) -> None:
        summary = summarize(loan_mortgage(), [by_amount(24, "20000")])
        assert all(row.payment == D("843.21") for row in summary.schedule[:-1])
        assert summary.schedule[-1].payment < D("843.21")
        assert summary.number_of_payments == 309
        assert summary.payments_saved == 51
        assert summary.current_payment == D("843.21")
        assert_consistent(loan_mortgage(), by_amount(24, "20000"))

    def test_by_periods_cuts_exactly_that_many_periods(self) -> None:
        summary = summarize(loan_mortgage(), [by_periods(24, 24)])
        assert summary.number_of_payments == 336
        assert summary.payments_saved == 24
        assert summary.schedule[23].early_amortization == D("9001.33")
        assert all(row.payment == D("843.21") for row in summary.schedule[:-1])
        assert abs(summary.schedule[-1].payment - D("843.21")) < D("1.00")
        assert_consistent(loan_mortgage(), by_periods(24, 24))

    def test_by_periods_all_remaining_cancels_the_loan(self) -> None:
        summary = summarize(loan_mortgage(), [by_periods(24, 336)])
        assert summary.number_of_payments == 24
        assert summary.schedule[-1].balance == D("0.00")
        assert summary.current_payment == D("0.00")

    def test_zero_interest(self) -> None:
        conditions = loan_mortgage(loan="12000", tin="0", years=1)
        summary = summarize(conditions, [by_periods(2, 3)])
        assert summary.schedule[1].early_amortization == D("3000.00")
        assert summary.number_of_payments == 9
        summary = summarize(conditions, [by_amount(2, "2500")])
        assert summary.number_of_payments == 10
        assert summary.schedule[-1].payment == D("500.00")
        assert_consistent(conditions, by_amount(2, "2500"))

    def test_annual_frequency(self) -> None:
        conditions = loan_mortgage(
            loan="100000", tin="5", years=10, frequency=PaymentFrequency.ANNUAL
        )
        summary = summarize(conditions, [by_periods(2, 3)])
        assert summary.number_of_payments == 7
        assert [row.year for row in summary.schedule] == list(range(1, 8))
        assert_consistent(conditions, by_periods(2, 3))

    def test_zero_payment_keeps_the_term(self) -> None:
        # 1 € over 600 months: the payment rounds to 0.00, the last period pays it all.
        conditions = loan_mortgage(loan="1", tin="0", years=50)
        schedule = amortization_schedule(conditions, [by_amount(10, "0.50")])
        assert len(schedule) == 600
        assert schedule[-1].payment == D("0.50")


class TestCombinedAmortizations:
    def test_capital_after_shortening_keeps_the_shortened_term(self) -> None:
        amortizations = [
            capital(12, "20000"),
            by_periods(24, 24),
            by_amount(60, "10000"),
            capital(100, "5000"),
        ]
        summary = summarize(loan_mortgage(), amortizations)
        before = summarize(loan_mortgage(), amortizations[:3])
        assert summary.number_of_payments == before.number_of_payments
        assert summary.current_payment < before.current_payment
        assert summary.total_early_amortized == sum(
            (row.early_amortization for row in summary.schedule), D("0")
        )
        assert_consistent(loan_mortgage(), *amortizations)

    def test_order_does_not_matter(self) -> None:
        first = amortization_schedule(loan_mortgage(), [capital(12, "1000"), by_periods(24, 2)])
        second = amortization_schedule(loan_mortgage(), [by_periods(24, 2), capital(12, "1000")])
        assert first == second


class TestAmortizationHelpers:
    def test_present_value_inverts_periodic_payment(self) -> None:
        assert present_value(D("843.21"), D("0.0025"), 360) == D("200000.46")
        assert present_value(D("100"), D("0"), 6) == D("600")
        assert present_value(D("100"), D("0.01"), 0) == D("0.00")

    def test_periods_to_repay(self) -> None:
        assert periods_to_repay(D("200000"), D("843.21"), D("0.0025")) == 360
        assert periods_to_repay(D("1000"), D("300"), D("0")) == 4


class TestAmortizationValidation:
    @pytest.mark.parametrize(
        ("kwargs", "field_name"),
        [
            ({"period": 0, "type": CAPITAL, "amount": D("1")}, "period"),
            ({"period": 1, "type": CAPITAL}, "amount"),
            ({"period": 1, "type": PERIODS, "amount": D("1"), "periods": 1}, "amount"),
            ({"period": 1, "type": CAPITAL, "periods": 1}, "periods"),
            ({"period": 1, "type": CAPITAL, "amount": D("0")}, "amount"),
            ({"period": 1, "type": PERIODS, "periods": 0}, "periods"),
        ],
    )
    def test_rules(self, kwargs: dict[str, object], field_name: str) -> None:
        with pytest.raises(MortgageValidationError) as exc:
            EarlyAmortization(**kwargs)  # pyright: ignore[reportArgumentType]
        assert exc.value.field_name == field_name

    @pytest.mark.parametrize(
        ("amortizations", "field_name", "message"),
        [
            ([capital(12, "199999")], "amount", "period 12: must not exceed"),
            ([by_periods(12, 349)], "periods", "period 12: must be at most 348"),
            ([capital(360, "1")], "period", "period 360: the loan is already paid off"),
            ([capital(361, "1")], "period", "period 361: the loan is already paid off"),
            (
                [by_periods(12, 348), capital(13, "1")],
                "period",
                "period 13: the loan is already paid off",
            ),
            (
                [capital(12, "1"), by_amount(12, "1")],
                "period",
                "period 12: only one amortization per period",
            ),
        ],
    )
    def test_schedule_rules(
        self, amortizations: list[EarlyAmortization], field_name: str, message: str
    ) -> None:
        with pytest.raises(MortgageValidationError) as exc:
            amortization_schedule(loan_mortgage(), amortizations)
        assert exc.value.field_name == field_name
        assert exc.value.message.startswith(message)


def dated(
    start: date,
    frequency: PaymentFrequency = PaymentFrequency.MONTHLY,
    tin: str = "3",
) -> MortgageConditions:
    return MortgageConditions(
        tin=D(tin), years=30, frequency=frequency, loan=D("200000"), start_date=start
    )


class TestStartDate:
    """Signed 15 Mar 2027: 15..31 Mar pay interest only, regular payments from April."""

    @pytest.mark.parametrize(
        ("start", "days"),
        [
            (date(2027, 3, 15), 17),
            (date(2027, 2, 1), 28),
            (date(2028, 2, 1), 29),
            (date(2027, 1, 31), 1),
        ],
    )
    def test_stub_days(self, start: date, days: int) -> None:
        assert stub_days(start) == days

    def test_stub_row(self) -> None:
        stub = amortization_schedule(dated(date(2027, 3, 15)))[0]
        # 200,000 · 3% · 17 / 365
        assert stub.period == 0
        assert stub.date == date(2027, 3, 1)
        assert stub.interest == D("279.45")
        assert stub.payment == D("279.45")
        assert stub.principal == D("0.00")
        assert stub.early_amortization == D("0.00")
        assert stub.balance == D("200000.00")
        assert stub.amortized == D("0.00")

    def test_signed_on_the_first_pays_the_whole_month(self) -> None:
        stub = amortization_schedule(dated(date(2027, 2, 1)))[0]
        assert stub.interest == D("460.27")

    def test_zero_rate_stub(self) -> None:
        stub = amortization_schedule(dated(date(2027, 3, 15), tin="0"))[0]
        assert stub.payment == D("0.00")

    def test_regular_periods_are_unchanged(self) -> None:
        plain = amortization_schedule(loan_mortgage())
        schedule = amortization_schedule(dated(date(2027, 3, 15)))
        assert len(schedule) == 361
        for row, base in zip(schedule[1:], plain, strict=True):
            assert (row.period, row.year, row.payment, row.balance) == (
                base.period,
                base.year,
                base.payment,
                base.balance,
            )
        assert all(row.date is None for row in plain)

    def test_monthly_dates(self) -> None:
        schedule = amortization_schedule(dated(date(2027, 3, 15)))
        assert schedule[1].date == date(2027, 4, 1)
        assert schedule[9].date == date(2027, 12, 1)
        assert schedule[10].date == date(2028, 1, 1)
        assert schedule[-1].date == date(2057, 3, 1)

    def test_annual_dates(self) -> None:
        schedule = amortization_schedule(dated(date(2027, 12, 31), PaymentFrequency.ANNUAL))
        assert schedule[0].date == date(2027, 12, 1)
        assert schedule[0].interest == D("16.44")
        assert schedule[1].date == date(2028, 12, 1)
        assert schedule[-1].date == date(2057, 12, 1)

    def test_summary(self) -> None:
        conditions = dated(date(2027, 3, 15))
        plain = summarize(loan_mortgage())
        summary = summarize(conditions)
        assert summary.number_of_payments == 360
        assert summary.payment == plain.payment
        assert summary.total_interest == plain.total_interest + D("279.45")
        assert summary.total_paid == summary.loan_amount + summary.total_interest
        assert summary.end_date == date(2057, 3, 1)
        assert plain.end_date is None

    def test_amortizations(self) -> None:
        conditions = dated(date(2027, 3, 15))
        summary = summarize(conditions, [by_periods(12, 12)])
        assert summary.payments_saved == 12
        assert summary.number_of_payments == 348
        assert summary.end_date == date(2056, 3, 1)
        assert summary.schedule[12].early_amortization > D("0")
        assert (
            summary.interest_saved
            == summarize(loan_mortgage(), [by_periods(12, 12)]).interest_saved
        )
