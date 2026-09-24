import re
from collections.abc import Sequence

from sqlmodel import Session, col, select

from rubit.persistence.models import MortgageRecord

DEFAULT_NAME_PATTERN = re.compile(r"^Mortgage (\d+)$")


class MortgageRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def all(self) -> Sequence[MortgageRecord]:
        return self._session.exec(select(MortgageRecord).order_by(col(MortgageRecord.id))).all()

    def get(self, mortgage_id: int) -> MortgageRecord | None:
        return self._session.get(MortgageRecord, mortgage_id)

    def get_many(self, mortgage_ids: Sequence[int]) -> list[MortgageRecord]:
        """Return the records in the requested order, skipping ids that don't exist."""
        statement = select(MortgageRecord).where(col(MortgageRecord.id).in_(mortgage_ids))
        by_id = {record.id: record for record in self._session.exec(statement)}
        return [by_id[i] for i in mortgage_ids if i in by_id]

    def save(self, record: MortgageRecord) -> MortgageRecord:
        self._session.add(record)
        self._session.commit()
        self._session.refresh(record)
        return record

    def delete(self, record: MortgageRecord) -> None:
        self._session.delete(record)
        self._session.commit()

    def next_default_name(self) -> str:
        """``Mortgage N`` with the smallest N not already used by a default-style name."""
        used: set[int] = set()
        for name in self._session.exec(select(MortgageRecord.name)):
            match = DEFAULT_NAME_PATTERN.match(name)
            if match:
                used.add(int(match.group(1)))
        n = 1
        while n in used:
            n += 1
        return f"Mortgage {n}"
