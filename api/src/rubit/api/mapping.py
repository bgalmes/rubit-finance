"""Conversions between HTTP schemas, database records and domain objects."""

from collections.abc import Sequence
from dataclasses import asdict

from rubit.api.schemas import (
    AmortizationOut,
    AmortizationRowOut,
    LoanMortgageIn,
    MortgageDetailOut,
    MortgageOut,
    PurchaseMortgageIn,
)
from rubit.domain import MortgageConditions, MortgageSummary, PurchaseInfo, summarize
from rubit.persistence import AmortizationRecord, MortgageMode, MortgageRecord

type MortgageInput = PurchaseMortgageIn | LoanMortgageIn


def to_conditions(payload: MortgageInput) -> MortgageConditions:
    """Build the domain conditions, raising ``MortgageValidationError`` on invalid input."""
    if isinstance(payload, PurchaseMortgageIn):
        purchase = PurchaseInfo(
            price=payload.purchase_price,
            savings=payload.initial_savings,
            expenses=payload.initial_expenses,
        )
        return MortgageConditions(
            tin=payload.tin,
            years=payload.years,
            frequency=payload.frequency,
            purchase=purchase,
            start_date=payload.start_date,
        )
    return MortgageConditions(
        tin=payload.tin,
        years=payload.years,
        frequency=payload.frequency,
        loan=payload.loan_amount,
        start_date=payload.start_date,
    )


def new_record(name: str, payload: MortgageInput) -> MortgageRecord:
    record = MortgageRecord(
        name=name,
        mode=payload.mode,
        tin=payload.tin,
        years=payload.years,
        frequency=payload.frequency,
    )
    apply_input(record, payload)
    return record


def apply_input(record: MortgageRecord, payload: MortgageInput) -> None:
    """Copy the payload onto ``record``, clearing the fields of the other mode."""
    record.mode = payload.mode
    record.tin = payload.tin
    record.years = payload.years
    record.frequency = payload.frequency
    record.start_date = payload.start_date
    if isinstance(payload, PurchaseMortgageIn):
        record.purchase_price = payload.purchase_price
        record.initial_savings = payload.initial_savings
        record.initial_expenses = payload.initial_expenses
        record.loan_amount = None
    else:
        record.purchase_price = None
        record.initial_savings = None
        record.initial_expenses = None
        record.loan_amount = payload.loan_amount


def _to_out(record: MortgageRecord, summary: MortgageSummary) -> MortgageOut:
    assert record.id is not None
    is_purchase = record.mode is MortgageMode.PURCHASE
    return MortgageOut(
        id=record.id,
        name=record.name,
        mode=record.mode,
        tin=record.tin,
        years=record.years,
        frequency=record.frequency,
        start_date=record.start_date,
        end_date=summary.end_date,
        purchase_price=record.purchase_price if is_purchase else None,
        initial_savings=record.initial_savings if is_purchase else None,
        initial_expenses=record.initial_expenses if is_purchase else None,
        down_payment=summary.down_payment,
        loan_amount=summary.loan_amount,
        purchase_percentage=summary.purchase_percentage,
        payment=summary.payment,
        current_payment=summary.current_payment,
        total_interest=summary.total_interest,
        total_paid=summary.total_paid,
        total_early_amortized=summary.total_early_amortized,
        number_of_payments=summary.number_of_payments,
        interest_saved=summary.interest_saved,
        payments_saved=summary.payments_saved,
    )


def _summarize(
    record: MortgageRecord, amortizations: Sequence[AmortizationRecord]
) -> MortgageSummary:
    return summarize(record.to_conditions(), [a.to_domain() for a in amortizations])


def to_out(record: MortgageRecord, amortizations: Sequence[AmortizationRecord]) -> MortgageOut:
    return _to_out(record, _summarize(record, amortizations))


def to_detail_out(
    record: MortgageRecord, amortizations: Sequence[AmortizationRecord]
) -> MortgageDetailOut:
    summary = _summarize(record, amortizations)
    early_by_period = {row.period: row.early_amortization for row in summary.schedule}
    return MortgageDetailOut(
        **_to_out(record, summary).model_dump(),
        amortizations=[
            AmortizationOut(
                period=a.period,
                type=a.type,
                amount=a.amount,
                periods=a.periods,
                applied_amount=early_by_period[a.period],
            )
            for a in amortizations
        ],
        schedule=[AmortizationRowOut(**asdict(row)) for row in summary.schedule],
    )
