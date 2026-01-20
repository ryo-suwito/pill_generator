from fastapi.testclient import TestClient
from issuance_service.main import app
import json
import base64

client = TestClient(app)

def test_issue_pill():
    response = client.post("/issue", json={"pid": "TEST-BATCH-001", "iat": 1737400000})
    assert response.status_code == 200
    data = response.json()
    assert "pill" in data

    pill = data["pill"]
    assert "." in pill
    payload_b64, signature = pill.split(".")

    # Check payload content
    padding = '=' * (-len(payload_b64) % 4)
    payload_json = base64.urlsafe_b64decode(payload_b64 + padding).decode('utf-8')
    payload = json.loads(payload_json)

    assert payload["pid"] == "TEST-BATCH-001"
    assert payload["iat"] == 1737400000
    assert payload["v"] == 1

def test_get_keys():
    response = client.get("/keys")
    assert response.status_code == 200
    data = response.json()
    assert "public_key" in data
