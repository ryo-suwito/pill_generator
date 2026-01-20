import os
import time
import jwt
import grpc
from fastapi import FastAPI, HTTPException, Header, Request
from pydantic import BaseModel
from typing import Optional
import httpx
from common.crypto import verify_pill
from common.models import SwapRequest, SwapResponse
from proto import subscription_pb2
from proto import subscription_pb2_grpc
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

app = FastAPI()

# Configuration
ISSUANCE_SERVICE_URL = os.environ.get("ISSUANCE_SERVICE_URL", "http://localhost:8000")
SUBSCRIPTION_SERVICE_HOST = os.environ.get("SUBSCRIPTION_SERVICE_HOST", "localhost")
SUBSCRIPTION_SERVICE_PORT = int(os.environ.get("SUBSCRIPTION_SERVICE_PORT", 50051))
INTERNAL_SERVICE_URL = os.environ.get("INTERNAL_SERVICE_URL", "http://localhost:8002")

# Generate RSA Keys for Internal JWT Signing (Gateway acts as Authority)
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
    backend=default_backend()
)
public_key = private_key.public_key()

GATEWAY_PRIVATE_PEM = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
)
GATEWAY_PUBLIC_PEM = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)

# Cache for Issuance Service Public Key
ISSUANCE_PUBLIC_KEY = None

async def get_issuance_public_key():
    global ISSUANCE_PUBLIC_KEY
    if ISSUANCE_PUBLIC_KEY:
        return ISSUANCE_PUBLIC_KEY

    # In test environment, we might need to mock this or set it manually
    if os.environ.get("MOCK_ISSUANCE_KEY"):
         ISSUANCE_PUBLIC_KEY = os.environ.get("MOCK_ISSUANCE_KEY")
         return ISSUANCE_PUBLIC_KEY

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{ISSUANCE_SERVICE_URL}/keys")
            if resp.status_code == 200:
                ISSUANCE_PUBLIC_KEY = resp.json()["public_key"]
                return ISSUANCE_PUBLIC_KEY
    except Exception as e:
        print(f"Failed to fetch public key: {e}")
        return None

@app.post("/swap", response_model=SwapResponse)
async def swap_pill(request: SwapRequest):
    pill = request.pill

    # 1. Verify Pill Signature
    issuance_pub_key = await get_issuance_public_key()
    if not issuance_pub_key:
        raise HTTPException(status_code=503, detail="Issuance public key unavailable")

    try:
        payload = verify_pill(issuance_pub_key, pill)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=f"Invalid Pill: {str(e)}")

    # 2. Burn Pill via gRPC
    if os.environ.get("MOCK_GRPC") != "true":
        try:
            # We use a context manager to ensure channel is closed, but creating channel per request is expensive.
            # In prod, reuse channel.
            with grpc.insecure_channel(f'{SUBSCRIPTION_SERVICE_HOST}:{SUBSCRIPTION_SERVICE_PORT}') as channel:
                stub = subscription_pb2_grpc.SubscriptionServiceStub(channel)
                burn_req = subscription_pb2.BurnRequest(pill_id=payload["pid"])
                burn_resp = stub.Burn(burn_req)

                if not burn_resp.success:
                    raise HTTPException(status_code=409, detail=f"Burn failed: {burn_resp.message}")
        except grpc.RpcError as e:
            raise HTTPException(status_code=503, detail=f"Subscription Service Unavailable: {e}")
    else:
        # Mock logic
        if payload["pid"] == "used_pill":
             raise HTTPException(status_code=409, detail="Burn failed: Double spend detected")

    # 3. Issue Internal JWT
    internal_payload = {
        "sub": payload["pid"],
        "exp": time.time() + 300,
        "iat": time.time(),
        "iss": "gateway-service"
    }

    token = jwt.encode(internal_payload, GATEWAY_PRIVATE_PEM, algorithm="RS256")

    return SwapResponse(token=token, expires_in=300)

@app.get("/keys")
def get_gateway_keys():
    """
    Expose Gateway Public Key for Internal Services.
    """
    return {"public_key": GATEWAY_PUBLIC_PEM.decode('utf-8')}

# Proxy logic is actually handled by client calling Gateway -> Gateway calls Internal.
# But "Authorize (Swap): Gateway swaps the User Session for a short-lived Internal JWT."
# "Access: Inner Services validate the Internal JWT locally using the Gateway Public Key."
# This implies the client gets the JWT and calls the Inner Services directly?
# Or Gateway proxies.
# "Gateway Proxy: The only node that checks the etcd state for current subscription validity."
# "Internal services are User-Agnostic and DB-Agnostic."
# Usually Gateway acts as a reverse proxy.
# If Gateway acts as reverse proxy, it strips the Pill/Session, adds Internal JWT, and forwards.
# Or it returns JWT to user, and user calls other services?
# "Gateway swaps the User Session for a short-lived Internal JWT."
# This sounds like an exchange.
# "Access: Inner Services validate the Internal JWT locally..."
# If user holds the Internal JWT, they can call Inner Services if they are exposed.
# If Inner Services are behind Gateway, Gateway passes the JWT.
# Let's assume Gateway proxies requests.

@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy(request: Request, path: str):
    # This endpoint simulates the "Gateway Proxy" role for accessing internal resources.
    # It expects the Internal JWT (if the client holds it) OR performs the swap transparently?
    # The architecture says "Gateway swaps the User Session for a short-lived Internal JWT".
    # And "Access: Inner Services validate the Internal JWT locally".

    # Scenario A: Client sends Pill/Session to Gateway. Gateway validates, mints JWT, calls Internal Service with JWT.
    # Scenario B: Client swaps Pill for JWT. Client calls Internal Service (or Gateway acting as router) with JWT.

    # Given "Gateway Proxy: The only node that checks the etcd state...", it suggests Gateway handles the check.
    # If the check is "Subscription Validity", that's the "Swap" phase (Burn).

    # Let's implement a simple proxy that forwards if a valid Internal JWT is present.
    # Or simpler: The /swap endpoint is the "Authorize" step.
    # The user then uses the JWT to access resources.
    pass
