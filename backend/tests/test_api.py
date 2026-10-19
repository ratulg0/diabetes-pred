from __future__ import annotations

from fastapi.testclient import TestClient


PAYLOAD = {
    "pregnancies": 1,
    "glucose": 110,
    "blood_pressure": 72,
    "skin_thickness": 25,
    "insulin": 90,
    "bmi": 28.5,
    "diabetes_pedigree_function": 0.45,
    "age": 32,
}


def test_health_and_ready(client: TestClient) -> None:
    assert client.get("/api/v1/health").json() == {"status": "ok"}
    assert client.get("/api/v1/ready").json()["status"] == "ready"


def test_predict_validation_rejects_unknown_outcome(client: TestClient) -> None:
    response = client.post("/api/v1/assessments/predict", json={**PAYLOAD, "Outcome": 1})
    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


def test_persist_list_and_dashboard(client: TestClient) -> None:
    created = client.post("/api/v1/assessments", json=PAYLOAD)
    assert created.status_code == 201
    record = created.json()
    assert record["prediction_id"] != "not-persisted"
    assert record["probability"] is None
    assert "not a diagnosis" in record["disclaimer"].lower()

    history = client.get("/api/v1/assessments?page_size=10").json()
    assert history["total_count"] == 1
    assert history["items"][0]["prediction_id"] == record["prediction_id"]
    assert client.get(f"/api/v1/assessments/{record['prediction_id']}").status_code == 200
    assert client.get("/api/v1/dashboard/summary").json()["total_assessments"] == 1
    assert client.delete(f"/api/v1/assessments/{record['prediction_id']}").status_code == 403


def test_preferences_round_trip(client: TestClient) -> None:
    assert client.get("/api/v1/preferences").status_code == 200
    response = client.put("/api/v1/preferences", json={"glucose_unit": "mmol/L", "compact_tables": True, "assessment_notifications": False})
    assert response.status_code == 200
    assert response.json()["glucose_unit"] == "mmol/L"
