import base64
from pathlib import Path

from fastapi.testclient import TestClient

from app.api import routes
from app.api.state import build_default_state
from app.main import create_app


def _upload_payload(name: str):
    pdf = Path(__file__).resolve().parents[2] / "data" / "tenders" / name
    data = "data:application/pdf;base64," + base64.b64encode(pdf.read_bytes()).decode()
    return {"file_name": name, "mime_type": "application/pdf", "file_data": data}


def _client():
    return TestClient(create_app(build_default_state()))


def test_tender_a_upload_creates_case_and_evaluates():
    client = _client()
    response = client.post("/api/v1/reviews/intake", json=_upload_payload("Tender_A.pdf"))
    assert response.status_code == 200
    body = response.json()
    assert body["tender"]["id"] == "TND-001"
    assert body["requirements"][0]["source_page"] == 7
    assert body["evaluation"]["summary"] == {"FAIL": 1, "PASS": 3}


def test_tender_b_upload_uses_new_threshold():
    client = _client()
    response = client.post("/api/v1/reviews/intake", json=_upload_payload("Tender_B.pdf"))
    assert response.status_code == 200
    body = response.json()
    assert body["tender"]["id"] == "TND-002"
    assert body["requirements"][0]["source_page"] == 5
    assert body["evaluation"]["summary"] == {"PASS": 4}


def test_passport_history_accumulates_reviewed_tenders():
    client = _client()
    client.post("/api/v1/reviews/intake", json=_upload_payload("Tender_A.pdf"))
    client.post("/api/v1/reviews/intake", json=_upload_payload("Tender_B.pdf"))
    response = client.get("/api/v1/bidders/BIDDER-001/passport")
    assert response.status_code == 200
    ids = [item["tender_id"] for item in response.json()["tender_history"]]
    assert ids == ["TND-001", "TND-002"]
