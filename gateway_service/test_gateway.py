from fastapi.testclient import TestClient
from gateway_service.main import app, get_gateway_keys
from common.crypto import generate_keypair, sign_payload
import os
import pytest
import jwt
from unittest.mock import patch, AsyncMock, MagicMock

client = TestClient(app)

# Helper to generate a pill
def generate_valid_pill(pid="TEST-123"):
    priv, pub = generate_keypair()
    # Mock the Issuance key retrieval to return this pub key
    os.environ["MOCK_ISSUANCE_KEY"] = pub
    payload = {"v": 1, "pid": pid, "iat": 1737400000}
    return sign_payload(priv, payload)

def test_get_keys():
    response = client.get("/keys")
    assert response.status_code == 200
    assert "public_key" in response.json()

@patch('httpx.AsyncClient.get', new_callable=AsyncMock)
def test_swap_success(mock_get):
    # Setup mock for Issuance Service keys
    priv, pub = generate_keypair()

    # We need to ensure resp.json() returns a dict, not a coroutine
    # Because mock_get is an AsyncMock, its return value is a coroutine (awaitable).
    # But inside the function we do `resp = await client.get()`. So resp is the result.
    # We want resp.json() to return a value.

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"public_key": pub}

    mock_get.return_value = mock_response

    # Clear any previous cached key
    import gateway_service.main
    gateway_service.main.ISSUANCE_PUBLIC_KEY = None

    # Generate Pill
    payload = {"v": 1, "pid": "TEST-SWAP-001", "iat": 1737400000}
    pill = sign_payload(priv, payload)

    # Enable Mock gRPC
    os.environ["MOCK_GRPC"] = "true"

    response = client.post("/swap", json={"pill": pill})
    assert response.status_code == 200
    data = response.json()
    assert "token" in data

    # Verify the returned JWT
    gateway_pub = client.get("/keys").json()["public_key"]
    # RS256 requires PyJWT[crypto] or cryptography installed.
    decoded = jwt.decode(data["token"], gateway_pub, algorithms=["RS256"])
    assert decoded["sub"] == "TEST-SWAP-001"

@patch('httpx.AsyncClient.get', new_callable=AsyncMock)
def test_swap_double_spend(mock_get):
    priv, pub = generate_keypair()

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"public_key": pub}

    mock_get.return_value = mock_response

    import gateway_service.main
    gateway_service.main.ISSUANCE_PUBLIC_KEY = None

    payload = {"v": 1, "pid": "used_pill", "iat": 1737400000}
    pill = sign_payload(priv, payload)

    os.environ["MOCK_GRPC"] = "true"

    response = client.post("/swap", json={"pill": pill})
    assert response.status_code == 409
