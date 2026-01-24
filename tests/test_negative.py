import pytest
import requests
import json
import base64

def test_double_spend(base_urls, unique_pid):
    """
    Verifies that a pill cannot be burnt twice.
    """
    # 1. Issue
    issue_payload = {"pid": unique_pid, "iat": 1715000000}
    resp = requests.post(f"{base_urls['issuance']}/Issue", json=issue_payload)
    assert resp.status_code == 200
    pill_string = resp.json()["pill"]

    # 2. Burn First Time (Success)
    resp = requests.post(f"{base_urls['gateway']}/Swap", json={"pill": pill_string})
    assert resp.status_code == 200

    # 3. Burn Second Time (Fail)
    resp = requests.post(f"{base_urls['gateway']}/Swap", json={"pill": pill_string})
    assert resp.status_code == 400
    assert "Double spend" in resp.text or "Burn failed" in resp.text

def test_invalid_signature(base_urls):
    """
    Verifies that tampering with the pill signature causes rejection.
    """
    # 1. Issue Valid Pill
    issue_payload = {"pid": "tamper_test", "iat": 1715000000}
    resp = requests.post(f"{base_urls['issuance']}/Issue", json=issue_payload)
    pill_string = resp.json()["pill"]

    # 2. Tamper with it
    # Format is Base64Payload.HexSignature
    parts = pill_string.split('.')
    assert len(parts) == 2
    
    # Change last char of signature
    tampered_sig = list(parts[1])
    tampered_sig[-1] = '0' if tampered_sig[-1] != '0' else '1'
    tampered_sig = "".join(tampered_sig)
    
    tampered_pill = f"{parts[0]}.{tampered_sig}"

    # 3. Try to Burn
    resp = requests.post(f"{base_urls['gateway']}/Swap", json={"pill": tampered_pill})
    assert resp.status_code == 400
    data = resp.json()
    assert "Invalid signature" in str(data) or "malformed" in str(data)

def test_malformed_pill(base_urls):
    """
    Verifies behavior with garbage input.
    """
    resp = requests.post(f"{base_urls['gateway']}/Swap", json={"pill": "garbage.input"})
    assert resp.status_code == 400
