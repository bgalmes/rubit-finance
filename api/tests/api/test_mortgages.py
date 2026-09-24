from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from rubit.api.app import Settings, create_app, find_web_dir

Payload = dict[str, Any]


def create(client: TestClient, payload: Payload) -> Payload:
    response = client.post("/api/mortgages", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


class TestCreate:
    def test_loan_mode(self, client: TestClient, reference_loan: Payload) -> None:
        body = create(client, reference_loan)
        assert body["name"] == "Mortgage 1"
        assert body["mode"] == "loan"
        assert body["loan_amount"] == "200000.00"
        assert body["payment"] == "843.21"
        assert body["purchase_price"] is None
        assert body["initial_savings"] is None
        assert body["down_payment"] is None
        assert body["purchase_percentage"] is None
        assert body["frequency"] == "monthly"
        assert len(body["schedule"]) == 360
        assert body["schedule"][-1]["balance"] == "0.00"
        assert Decimal(body["total_paid"]) == Decimal(body["loan_amount"]) + Decimal(
            body["total_interest"]
        )

    def test_purchase_mode(self, client: TestClient, reference_purchase: Payload) -> None:
        body = create(client, reference_purchase)
        assert body["name"] == "Flat in town"
        assert body["loan_amount"] == "200000.00"
        assert body["down_payment"] == "50000"
        assert body["purchase_percentage"] == "80.00"
        assert body["payment"] == "843.21"

    def test_purchase_defaults(self, client: TestClient) -> None:
        body = create(
            client, {"mode": "purchase", "purchase_price": "100000", "tin": "2", "years": 10}
        )
        assert body["initial_savings"] == "0"
        assert body["initial_expenses"] == "0"
        assert body["loan_amount"] == "100000.00"

    def test_default_names_fill_gaps(self, client: TestClient, reference_loan: Payload) -> None:
        first = create(client, reference_loan)
        create(client, reference_loan)
        client.delete(f"/api/mortgages/{first['id']}")
        assert create(client, reference_loan)["name"] == "Mortgage 1"
        assert create(client, reference_loan)["name"] == "Mortgage 3"

    def test_blank_name_gets_default(self, client: TestClient, reference_loan: Payload) -> None:
        assert create(client, {**reference_loan, "name": "   "})["name"] == "Mortgage 1"

    def test_annual_frequency(self, client: TestClient) -> None:
        payload = {"mode": "loan", "loan_amount": "100000", "tin": "5", "years": 10}
        body = create(client, {**payload, "frequency": "annual"})
        assert body["payment"] == "12950.46"
        assert len(body["schedule"]) == 10


class TestValidation:
    @pytest.mark.parametrize(
        ("changes", "field"),
        [
            ({"tin": "100.5"}, "tin"),
            ({"tin": "-1"}, "tin"),
            ({"years": 0}, "years"),
            ({"years": 51}, "years"),
            ({"loan_amount": "0"}, "loan_amount"),
            ({"loan_amount": "10.001"}, "loan_amount"),
            ({"frequency": "weekly"}, "frequency"),
        ],
    )
    def test_field_rules(
        self, client: TestClient, reference_loan: Payload, changes: Payload, field: str
    ) -> None:
        response = client.post("/api/mortgages", json={**reference_loan, **changes})
        assert response.status_code == 422
        assert any(field in error["loc"] for error in response.json()["detail"])

    def test_savings_must_leave_something_to_borrow(
        self, client: TestClient, reference_purchase: Payload
    ) -> None:
        payload = {**reference_purchase, "initial_savings": "270000"}
        response = client.post("/api/mortgages", json=payload)
        assert response.status_code == 422
        assert response.json()["detail"] == [
            {
                "type": "value_error",
                "loc": ["body", "initial_savings"],
                "msg": "must be less than purchase price + initial expenses",
            }
        ]

    def test_unknown_mode(self, client: TestClient, reference_loan: Payload) -> None:
        response = client.post("/api/mortgages", json={**reference_loan, "mode": "lease"})
        assert response.status_code == 422

    def test_fields_of_other_mode_are_rejected(
        self, client: TestClient, reference_loan: Payload
    ) -> None:
        payload = {**reference_loan, "purchase_price": "1000"}
        assert client.post("/api/mortgages", json=payload).status_code == 422


class TestReadUpdateDelete:
    def test_list(
        self, client: TestClient, reference_loan: Payload, reference_purchase: Payload
    ) -> None:
        assert client.get("/api/mortgages").json() == []
        create(client, reference_loan)
        create(client, reference_purchase)
        body = client.get("/api/mortgages").json()
        assert [m["name"] for m in body] == ["Mortgage 1", "Flat in town"]
        assert "schedule" not in body[0]

    def test_get(self, client: TestClient, reference_loan: Payload) -> None:
        created = create(client, reference_loan)
        response = client.get(f"/api/mortgages/{created['id']}")
        assert response.status_code == 200
        assert response.json() == created

    def test_get_missing(self, client: TestClient) -> None:
        assert client.get("/api/mortgages/999").status_code == 404

    def test_update_switches_mode(
        self, client: TestClient, reference_loan: Payload, reference_purchase: Payload
    ) -> None:
        created = create(client, reference_loan)
        response = client.put(f"/api/mortgages/{created['id']}", json=reference_purchase)
        assert response.status_code == 200
        body = response.json()
        assert body["mode"] == "purchase"
        assert body["name"] == "Flat in town"
        assert body["purchase_price"] == "250000"
        assert body["purchase_percentage"] == "80.00"

        response = client.put(f"/api/mortgages/{created['id']}", json=reference_loan)
        body = response.json()
        assert body["name"] == "Flat in town"  # blank name keeps the current one
        assert body["mode"] == "loan"
        assert body["purchase_price"] is None

    def test_update_invalid_keeps_record(
        self, client: TestClient, reference_purchase: Payload
    ) -> None:
        created = create(client, reference_purchase)
        bad = {**reference_purchase, "initial_savings": "999999"}
        assert client.put(f"/api/mortgages/{created['id']}", json=bad).status_code == 422
        assert client.get(f"/api/mortgages/{created['id']}").json() == created

    def test_update_missing(self, client: TestClient, reference_loan: Payload) -> None:
        assert client.put("/api/mortgages/999", json=reference_loan).status_code == 404

    def test_delete(self, client: TestClient, reference_loan: Payload) -> None:
        created = create(client, reference_loan)
        assert client.delete(f"/api/mortgages/{created['id']}").status_code == 204
        assert client.get(f"/api/mortgages/{created['id']}").status_code == 404
        assert client.delete(f"/api/mortgages/{created['id']}").status_code == 404


class TestCompare:
    def test_compare_keeps_requested_order(
        self, client: TestClient, reference_loan: Payload, reference_purchase: Payload
    ) -> None:
        loan = create(client, reference_loan)
        purchase = create(client, reference_purchase)
        response = client.get(f"/api/mortgages/compare?ids={purchase['id']},{loan['id']}")
        assert response.status_code == 200
        columns = response.json()["mortgages"]
        assert [c["id"] for c in columns] == [purchase["id"], loan["id"]]
        assert columns[0]["down_payment"] == "50000"
        # Loan-mode mortgages have no purchase data; the UI shows "—".
        for key in ("purchase_price", "initial_savings", "initial_expenses", "down_payment"):
            assert columns[1][key] is None
        assert columns[1]["purchase_percentage"] is None
        assert "schedule" not in columns[0]

    def test_compare_missing(self, client: TestClient, reference_loan: Payload) -> None:
        created = create(client, reference_loan)
        response = client.get(f"/api/mortgages/compare?ids={created['id']},42")
        assert response.status_code == 404
        assert "42" in response.json()["detail"]

    def test_compare_bad_ids(self, client: TestClient) -> None:
        assert client.get("/api/mortgages/compare?ids=1,abc").status_code == 422
        assert client.get("/api/mortgages/compare").status_code == 422


class TestSpa:
    @pytest.fixture
    def spa_client(self, tmp_path: Path) -> TestClient:
        # Mirrors `nuxt generate` output: 404.html and per-route folders included.
        web_dir = tmp_path / "public"
        (web_dir / "_nuxt").mkdir(parents=True)
        (web_dir / "compare").mkdir()
        (web_dir / "index.html").write_text("<html>rubit spa</html>")
        (web_dir / "404.html").write_text("<html>nuxt 404</html>")
        (web_dir / "compare" / "index.html").write_text("<html>rubit spa</html>")
        (web_dir / "_nuxt" / "app.js").write_text("console.log('rubit')")
        app = create_app(Settings(db_path=tmp_path / "rubit.db", web_dir=web_dir))
        return TestClient(app, follow_redirects=False)

    def test_serves_index_and_assets(self, spa_client: TestClient) -> None:
        with spa_client:
            assert "rubit spa" in spa_client.get("/").text
            assert "console.log" in spa_client.get("/_nuxt/app.js").text

    @pytest.mark.parametrize(
        "path", ["/compare", "/compare/", "/mortgages/new", "/mortgages/3", "/mortgages/3/edit"]
    )
    def test_client_routes_fall_back_to_index(self, spa_client: TestClient, path: str) -> None:
        with spa_client:
            response = spa_client.get(path)
            assert response.status_code == 200
            assert "rubit spa" in response.text

    def test_unknown_api_paths_get_json_404(self, spa_client: TestClient) -> None:
        with spa_client:
            assert spa_client.get("/api/mortgages").json() == []
            for path in ("/api", "/api/unknown", "/api/mortgages/1/nope"):
                response = spa_client.get(path)
                assert response.status_code == 404
                assert response.json() == {"detail": "Not Found"}

    def test_find_web_dir_env(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("RUBIT_WEB_DIR", str(tmp_path))
        assert find_web_dir() is None
        (tmp_path / "index.html").write_text("x")
        assert find_web_dir() == tmp_path
