from collections.abc import Iterator
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request, status
from sqlmodel import Session

from rubit.api.mapping import apply_input, new_record, to_conditions, to_detail_out, to_out
from rubit.api.schemas import ComparisonOut, MortgageDetailOut, MortgageIn, MortgageOut
from rubit.persistence import MortgageRecord, MortgageRepository

router = APIRouter(prefix="/api/mortgages", tags=["mortgages"])


def get_repository(request: Request) -> Iterator[MortgageRepository]:
    with Session(request.app.state.engine) as session:
        yield MortgageRepository(session)


Repository = Annotated[MortgageRepository, Depends(get_repository)]
Payload = Annotated[MortgageIn, Body()]


def _get_or_404(repository: MortgageRepository, mortgage_id: int) -> MortgageRecord:
    record = repository.get(mortgage_id)
    if record is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Mortgage {mortgage_id} not found")
    return record


@router.get("")
def list_mortgages(repository: Repository) -> list[MortgageOut]:
    return [to_out(record) for record in repository.all()]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_mortgage(payload: Payload, repository: Repository) -> MortgageDetailOut:
    to_conditions(payload)
    name = payload.name or repository.next_default_name()
    return to_detail_out(repository.save(new_record(name, payload)))


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
    return ComparisonOut(mortgages=[to_out(record) for record in records])


@router.get("/{mortgage_id}")
def get_mortgage(mortgage_id: int, repository: Repository) -> MortgageDetailOut:
    return to_detail_out(_get_or_404(repository, mortgage_id))


@router.put("/{mortgage_id}")
def update_mortgage(
    mortgage_id: int, payload: Payload, repository: Repository
) -> MortgageDetailOut:
    record = _get_or_404(repository, mortgage_id)
    to_conditions(payload)
    apply_input(record, payload)
    if payload.name:
        record.name = payload.name
    return to_detail_out(repository.save(record))


@router.delete("/{mortgage_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_mortgage(mortgage_id: int, repository: Repository) -> None:
    repository.delete(_get_or_404(repository, mortgage_id))
