import os
from fastapi import FastAPI, Depends, HTTPException, Header
import jwt
import httpx
import asyncio

app = FastAPI()

GATEWAY_SERVICE_URL = os.environ.get("GATEWAY_SERVICE_URL", "http://localhost:8001")
GATEWAY_PUBLIC_KEY = None

async def get_gateway_public_key():
    global GATEWAY_PUBLIC_KEY
    if GATEWAY_PUBLIC_KEY:
        return GATEWAY_PUBLIC_KEY

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{GATEWAY_SERVICE_URL}/keys")
            if resp.status_code == 200:
                GATEWAY_PUBLIC_KEY = resp.json()["public_key"]
                return GATEWAY_PUBLIC_KEY
    except Exception as e:
        print(f"Failed to fetch gateway public key: {e}")
        return None

async def verify_token(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Bearer token")

    token = authorization.split(" ")[1]

    public_key = await get_gateway_public_key()
    if not public_key:
        raise HTTPException(status_code=503, detail="Gateway public key unavailable")

    try:
        # Verify JWT signature using Gateway's Public Key
        # "Internal Services validate the Internal JWT locally using the Gateway Public Key. Database latency = 0ms."
        payload = jwt.decode(token, public_key, algorithms=["RS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

@app.get("/data")
async def get_protected_data(user_claims: dict = Depends(verify_token)):
    """
    Protected resource that requires a valid Internal JWT.
    """
    return {
        "message": "Access granted",
        "user_id": user_claims.get("sub"),
        "service": "Internal Service A"
    }

@app.get("/health")
def health_check():
    return {"status": "ok"}
