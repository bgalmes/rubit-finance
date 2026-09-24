"""Conversions between HTTP schemas, database records and domain objects."""

from dataclasses import asdict

from rubit.api.schemas import (
    AmortizationRowOut,
    LoanMortgageIn,
    MortgageDetailOut,
    MortgageOut,
    PurchaseMortgageIn,
)
from rubit.domain import MortgageConditions, MortgageSummary, PurchaseInfo, summarize
from rubit.persistence import MortgageMode, MortgageRecord

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
            tin=payload.tin, years=payload.years, frequency=payload.frequency, purchase=purchase
        )
    return MortgageConditions(
        tin=payload.tin, years=payload.years, frequency=payload.frequency, loan=payload.loan_amount
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
        purchase_price=record.purchase_price if is_purchase else None,
        initial_savings=record.initial_savings if is_purchase else None,
        initial_expenses=record.initial_expenses if is_purchase else None,
        down_payment=summary.down_payment,
        loan_amount=summary.loan_amount,
        purchase_percentage=summary.purchase_percentage,
        payment=summary.payment,
        total_interest=summary.total_interest,
        total_paid=summary.total_paid,
    )


def to_out(record: MortgageRecord) -> MortgageOut:
    return _to_out(record, summarize(record.to_conditions()))


def to_detail_out(record: MortgageRecord) -> MortgageDetailOut:
    summary = summarize(record.to_conditions())
    return MortgageDetailOut(
        **_to_out(record, summary).model_dump(),
        schedule=[AmortizationRowOut(**asdict(row)) for row in summary.schedule],
    )
