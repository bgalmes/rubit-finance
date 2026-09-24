from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from rubit.api.app import Settings, create_app


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    app = create_app(Settings(db_path=tmp_path / "data" / "rubit.db", web_dir=None))
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def reference_loan() -> dict[str, Any]:
    """PLAN.md reference example, entered as a loan amount."""
    return {"mode": "loan", "loan_amount": "200000", "tin": "3", "years": 30}


@pytest.fixture
def reference_purchase() -> dict[str, Any]:
    """Same 200,000 € loan, derived from a purchase: 250,000 + 20,000 − 70,000."""
    return {
        "mode": "purchase",
        "name": "Flat in town",
        "purchase_price": "250000",
        "initial_savings": "70000",
        "initial_expenses": "20000",
        "tin": "3",
        "years": 30,
        "frequency": "monthly",
    }
