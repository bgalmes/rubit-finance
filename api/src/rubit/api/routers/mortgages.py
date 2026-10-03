from collections.abc import Iterator
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, Request, status
from sqlmodel import Session

from rubit.api.mapping import apply_input, new_record, to_conditions, to_detail_out, to_out
from rubit.api.schemas import (
    AmortizationIn,
    ComparisonOut,
    MortgageDetailOut,
    MortgageIn,
    MortgageOut,
)
from rubit.domain import EarlyAmortization, summarize
from rubit.persistence import AmortizationRecord, MortgageRecord, MortgageRepository

router = APIRouter(prefix="/api/mortgages", tags=["mortgages"])


def get_repository(request: Request) -> Iterator[MortgageRepository]:
    with Session(request.app.state.engine) as session:
        yield MortgageRepository(session)


Repository = Annotated[MortgageRepository, Depends(get_repository)]
Payload = Annotated[MortgageIn, Body()]
Period = Annotated[int, Path(ge=1)]


def _get_or_404(repository: MortgageRepository, mortgage_id: int) -> MortgageRecord:
    record = repository.get(mortgage_id)
    if record is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Mortgage {mortgage_id} not found")
    return record


def _amortizations(
    repository: MortgageRepository, record: MortgageRecord
) -> list[AmortizationRecord]:
    assert record.id is not None
    return list(repository.amortizations(record.id))


def _detail(repository: MortgageRepository, record: MortgageRecord) -> MortgageDetailOut:
    return to_detail_out(record, _amortizations(repository, record))


@router.get("")
def list_mortgages(repository: Repository) -> list[MortgageOut]:
    return [to_out(record, _amortizations(repository, record)) for record in repository.all()]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_mortgage(payload: Payload, repository: Repository) -> MortgageDetailOut:
    to_conditions(payload)
    name = payload.name or repository.next_default_name()
    return to_detail_out(repository.save(new_record(name, payload)), [])


# Declared before /{mortgage_id} so "compare" isn't parsed as an id.
@router.get("/compare")
def compare_mortgages(
    repository: Repository,
    ids: Annotated[str, Query(description="Comma-separated mortgage ids, e.g. 1,2,3")],
) -> ComparisonOut:
    try:
        mortgage_ids = [int(part) for part in ids.split(",") if part.strip()]
    except ValueError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "ids must be comma-separated integers"
        ) from exc
    records = repository.get_many(mortgage_ids)
    missing = sorted(set(mortgage_ids) - {record.id for record in records})
    if missing:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Mortgages not found: {missing}")
    return ComparisonOut(
        mortgages=[to_out(record, _amortizations(repository, record)) for record in records]
    )


@router.get("/{mortgage_id}")
def get_mortgage(mortgage_id: int, repository: Repository) -> MortgageDetailOut:
    return _detail(repository, _get_or_404(repository, mortgage_id))


@router.put("/{mortgage_id}")
def update_mortgage(
    mortgage_id: int, payload: Payload, repository: Repository
) -> MortgageDetailOut:
    record = _get_or_404(repository, mortgage_id)
    if to_conditions(payload) != record.to_conditions():
        # Amortizations only make sense on the schedule they were entered on.
        repository.delete_amortizations(mortgage_id)
    apply_input(record, payload)
    if payload.name:
        record.name = payload.name
    return _detail(repository, repository.save(record))


@router.delete("/{mortgage_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_mortgage(mortgage_id: int, repository: Repository) -> None:
    repository.delete(_get_or_404(repository, mortgage_id))


@router.put("/{mortgage_id}/amortizations/{period}")
def save_amortization(
    mortgage_id: int,
    period: Period,
    payload: Annotated[AmortizationIn, Body()],
    repository: Repository,
) -> MortgageDetailOut:
    """Create or replace the early amortization made after ``period``'s payment."""
    record = _get_or_404(repository, mortgage_id)
    amortization = EarlyAmortization(
        period=period, type=payload.type, amount=payload.amount, periods=payload.periods
    )
    others = [a for a in _amortizations(repository, record) if a.period != period]
    summarize(record.to_conditions(), [*(a.to_domain() for a in others), amortization])
    stored = repository.get_amortization(mortgage_id, period) or AmortizationRecord(
        mortgage_id=mortgage_id, period=period, type=payload.type
    )
    stored.type = payload.type
    stored.amount = payload.amount
    stored.periods = payload.periods
    repository.save_amortization(stored)
    return _detail(repository, record)


@router.delete("/{mortgage_id}/amortizations/{period}")
def delete_amortization(
    mortgage_id: int, period: Period, repository: Repository
) -> MortgageDetailOut:
    record = _get_or_404(repository, mortgage_id)
    stored = repository.get_amortization(mortgage_id, period)
    if stored is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            f"Mortgage {mortgage_id} has no amortization at period {period}",
        )
    repository.delete_amortization(stored)
    return _detail(repository, record)
