"""FastAPI integration tests; no network calls or user data."""
from fastapi.testclient import TestClient
from agents.api import app

client = TestClient(app)


def test_static_console_is_served():
    page = client.get("/")
    assert page.status_code == 200
    assert "Rule-based task audit" in page.text
    js = client.get("/app.js")
    assert js.status_code == 200
    assert "function evaluate(data)" in js.text


def test_task_endpoint_validation_and_phi_error():
    base = {
        "task_id": "TEST-01", "target_identifier": "KEY-01",
        "primary_metric": 30.0, "secondary_metric": 0.0,
        "status_descriptor": "NOMINAL"
    }
    response = client.post("/api/audit", json=base)
    assert response.status_code == 200
    assert response.json()["overall_urgency"] == "ELEVATED_RISK"

    response = client.post("/api/audit", json={**base, "attributes": {"note": "MRN-123456"}})
    assert response.status_code == 422
    assert "Potential sensitive identifier" in response.json()["detail"]

    response = client.post("/api/audit", json={**base, "primary_metric": "NaN"})
    assert response.status_code == 422
