import pytest
import requests
import json
import base64

def test_claims_preservation(base_urls, unique_pid):
    """
    Verifies that extra data in the Pill payload (Recipe) is preserved in the final keyless-minted JWT (Wristband).
    """
    # 1. Issue with Extra Data (The "Recipe")
    contract_data = {
        "pid": unique_pid, 
        "iat": 1715000000,
        "access_level": "vip",
        "concert_id": "taylor_swift_eras",
        "seat_number": "A1"
    }
    
    # Note: IssueController takes PillPayload. The extra fields should be captured by [JsonExtensionData].
    resp = requests.post(f"{base_urls['issuance']}/Issue", json=contract_data)
    assert resp.status_code == 200, f"Issuance failed: {resp.text}"
    pill_string = resp.json()["pill"]
    
    # 2. Burn (Swap for Wristband)
    resp = requests.post(f"{base_urls['gateway']}/Swap", json={"pill": pill_string})
    assert resp.status_code == 200, f"Swap failed: {resp.text}"
    token = resp.json()["token"]
    
    # 3. Decode Token (Verify Wristband)
    # We don't have the secret to verify signature here (it's in Keyless), but we can decode the payload.
    # JWT is header.payload.signature
    parts = token.split('.')
    assert len(parts) == 3
    
    payload_json = base64.urlsafe_b64decode(parts[1] + "==").decode('utf-8')
    claims = json.loads(payload_json)
    
    print(f"Token Claims: {claims}")
    
    # 4. Verify Claims Preserved
    assert claims["sub"] == unique_pid
    assert claims["access_level"] == "vip"
    assert claims["concert_id"] == "taylor_swift_eras"
    assert claims["seat_number"] == "A1"
