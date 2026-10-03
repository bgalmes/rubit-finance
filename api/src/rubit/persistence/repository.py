import re
from collections.abc import Sequence

from sqlmodel import Session, col, select

from rubit.persistence.models import AmortizationRecord, MortgageRecord

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
        assert record.id is not None
        self._delete_amortizations(record.id)
        self._session.delete(record)
        self._session.commit()

    def amortizations(self, mortgage_id: int) -> Sequence[AmortizationRecord]:
        statement = (
            select(AmortizationRecord)
            .where(AmortizationRecord.mortgage_id == mortgage_id)
            .order_by(col(AmortizationRecord.period))
        )
        return self._session.exec(statement).all()

    def get_amortization(self, mortgage_id: int, period: int) -> AmortizationRecord | None:
        statement = select(AmortizationRecord).where(
            AmortizationRecord.mortgage_id == mortgage_id, AmortizationRecord.period == period
        )
        return self._session.exec(statement).first()

    def save_amortization(self, record: AmortizationRecord) -> None:
        self._session.add(record)
        self._session.commit()

    def delete_amortization(self, record: AmortizationRecord) -> None:
        self._session.delete(record)
        self._session.commit()

    def delete_amortizations(self, mortgage_id: int) -> None:
        self._delete_amortizations(mortgage_id)
        self._session.commit()

    def _delete_amortizations(self, mortgage_id: int) -> None:
        for amortization in self.amortizations(mortgage_id):
            self._session.delete(amortization)

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
