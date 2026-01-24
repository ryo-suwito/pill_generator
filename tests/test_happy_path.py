import pytest
import requests
import json
import base64

def test_full_lifecycle(base_urls, unique_pid):
    """
    Verifies the complete flow:
    1. Issue a pill
    2. Burn the pill (should trigger keyless storage)
    3. Verify key exists in keyless
    4. Use token to access internal resource
    """
    
    # 1. Issue Pill
    print(f"\n[Step 1] Issuing pill for PID: {unique_pid}")
    issue_payload = {"pid": unique_pid, "iat": 1715000000}
    resp = requests.post(f"{base_urls['issuance']}/Issue", json=issue_payload)
    assert resp.status_code == 200, f"Issuance failed: {resp.text}"
    pill_data = resp.json()
    assert "pill" in pill_data
    pill_string = pill_data["pill"]
    print(f"Issued Pill: {pill_string[:20]}...")

    # 2. Verify Key DOES NOT exist yet (it is created on burn)
    # The subscription service generates the key during burn.
    # Note: Neuer Keyless doesn't have a simple "Check Key" endpoint without knowing the content to verify or such
    # But we can try to "Mint" or "Verify" using it. If key doesn't exist, it should fail.
    # Actually, Neuer Keyless HTTP API has /verify but needs key_id. 
    # Let's try to verify a dummy token. If key doesn't exist, it should likely return specific error.
    # However, for robustness, we just rely on the fact that if Burn succeeds, Keyless worked.
    
    # 3. Burn Pill
    print(f"[Step 2] Burning pill...")
    swap_payload = {"pill": pill_string}
    resp = requests.post(f"{base_urls['gateway']}/Swap", json=swap_payload)
    
    assert resp.status_code == 200, f"Swap failed: {resp.text}"
    token_data = resp.json()
    assert "token" in token_data
    access_token = token_data["token"]
    print(f"Received Token: {access_token[:20]}...")

    # 4. Verify Key Storage in Keyless
    # Now that we burnt it, we expect the private key for `unique_pid` to be in Keyless.
    # We can test this by asking Keyless to Mint a JWT for us using this ID.
    # Reference: curl -X POST localhost:8090/mint -H "X-Key-ID: user123" -d ...
    print(f"[Step 3] Verifying Keyless storage...")
    keyless_payload = {"sub": "test_verification"}
    # Note: Using headers for X-Key-ID as per Keyless README
    resp = requests.post(
        f"{base_urls['keyless']}/mint", 
        headers={"X-Key-ID": unique_pid},
        json=keyless_payload
    )
    assert resp.status_code == 200, f"Keyless Mint failed (Key not found?): {resp.text}"
    minted_token = resp.text
    assert len(minted_token) > 20, "Minted token seems too short"
    print("Keyless successfully used stored key to mint token.")

    # 5. Access Protected Resource
    print(f"[Step 4] Accessing protected resource...")
    resp = requests.get(
        f"{base_urls['internal']}/Data", # Assuming standard endpoint or from README check
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert resp.status_code == 200, f"Access failed: {resp.text}"
    data = resp.json()
    assert data["message"] == "Access granted"
    assert data["user_id"] == unique_pid
    print("Protected resource accessed successfully.")
