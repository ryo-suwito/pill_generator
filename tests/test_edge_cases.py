import pytest
import requests
import time

def test_token_reuse(base_urls, unique_pid):
    """
    Verifies that the issued JWT is valid for multiple requests within its lifetime (5 min).
    """
    # 1. Issue & Burn
    issue_payload = {"pid": unique_pid, "iat": 1715000000}
    resp = requests.post(f"{base_urls['issuance']}/Issue", json=issue_payload)
    pill_string = resp.json()["pill"]
    
    resp = requests.post(f"{base_urls['gateway']}/Swap", json={"pill": pill_string})
    token = resp.json()["token"]

    # 2. Access Multiply
    for i in range(3):
        resp = requests.get(
            f"{base_urls['internal']}/Data",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200, f"Access {i} failed"

def test_access_without_token(base_urls):
    resp = requests.get(f"{base_urls['internal']}/Data")
    assert resp.status_code == 401

def test_access_with_bad_token(base_urls):
    resp = requests.get(
        f"{base_urls['internal']}/Data",
        headers={"Authorization": "Bearer bad.token.here"}
    )
    assert resp.status_code == 401

# Note: Concurrency testing works best with tools like locust or specialized scripts, 
# but simple loops in pytest can catch basic race conditions if run in parallel.
# For this suite, we focus on functional edge cases.
