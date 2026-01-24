import pytest
import os
import requests
import time

# Configuration from env vars or defaults
ISSUANCE_URL = os.getenv('ISSUANCE_URL', 'http://localhost:8000')
GATEWAY_URL = os.getenv('GATEWAY_URL', 'http://localhost:8001')
INTERNAL_URL = os.getenv('INTERNAL_URL', 'http://localhost:8002')
KEYLESS_URL = os.getenv('KEYLESS_URL', 'http://localhost:8090')

@pytest.fixture(scope="session")
def base_urls():
    return {
        "issuance": ISSUANCE_URL,
        "gateway": GATEWAY_URL,
        "internal": INTERNAL_URL,
        "keyless": KEYLESS_URL
    }

@pytest.fixture
def unique_pid():
    """Generates a unique Pill ID for each test"""
    return f"test_pill_{int(time.time())}_{os.urandom(4).hex()}"

def wait_for_service(url, timeout=30):
    """Helper to wait for service availability"""
    start = time.time()
    while time.time() - start < timeout:
        try:
            requests.get(url, timeout=1)
            return True
        except requests.RequestException:
            time.sleep(1)
    return False
