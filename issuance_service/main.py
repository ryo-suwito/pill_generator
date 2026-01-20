import os
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from common.crypto import generate_keypair, sign_payload
from common.models import IssueRequest, IssueResponse
import asyncio

app = FastAPI()

# In a real scenario, these keys would be loaded from a secure vault.
# For demo purposes, we generate them on startup and print them.
# The public key should be shared with the Gateway/Verifier.
PRIVATE_KEY_HEX, PUBLIC_KEY_HEX = generate_keypair()

print(f"ISSUANCE_SERVICE: Public Key: {PUBLIC_KEY_HEX}")
print(f"ISSUANCE_SERVICE: Private Key: {PRIVATE_KEY_HEX}")

# Mock Shadow DB
shadow_db = []

@app.post("/issue", response_model=IssueResponse)
async def issue_pill(request: IssueRequest):
    """
    Generates a cryptographically signed pill.
    """
    payload = {
        "v": 1,
        "pid": request.pid,
        "iat": request.iat
    }

    try:
        pill = sign_payload(PRIVATE_KEY_HEX, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Signing failed: {str(e)}")

    # Asynchronous Shadow DB recording
    # In real world, use a background task or message queue
    asyncio.create_task(record_shadow_db(payload))

    return IssueResponse(pill=pill)

async def record_shadow_db(payload: dict):
    # Simulate DB latency
    await asyncio.sleep(0.01)
    shadow_db.append(payload)
    # print(f"Recorded in Shadow DB: {payload['pid']}")

@app.get("/keys")
def get_keys():
    """
    Expose public key for other services (Gateway) to fetch.
    In prod, this might be distributed via config or a key server.
    """
    return {"public_key": PUBLIC_KEY_HEX}
