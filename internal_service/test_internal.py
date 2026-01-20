from fastapi.testclient import TestClient
from internal_service.main import app
import os
import pytest
import jwt
from unittest.mock import patch, AsyncMock, MagicMock
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

client = TestClient(app)

# Generate a temporary keypair to simulate Gateway
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
    backend=default_backend()
)
public_key = private_key.public_key()
PUBLIC_PEM = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
).decode('utf-8')

PRIVATE_PEM = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
)

@patch('httpx.AsyncClient.get', new_callable=AsyncMock)
def test_access_protected_data(mock_get):
    # Mock Gateway Key Response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"public_key": PUBLIC_PEM}
    mock_get.return_value = mock_response

    # Generate a valid token signed by "Gateway"
    token = jwt.encode({"sub": "user123"}, PRIVATE_PEM, algorithm="RS256")

    # Request
    response = client.get("/data", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["user_id"] == "user123"

@patch('httpx.AsyncClient.get', new_callable=AsyncMock)
def test_access_denied_invalid_token(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"public_key": PUBLIC_PEM}
    mock_get.return_value = mock_response

    response = client.get("/data", headers={"Authorization": "Bearer invalid_token"})
    assert response.status_code == 401
