import pytest
from common.crypto import generate_keypair, sign_payload, verify_pill

def test_crypto_flow():
    priv, pub = generate_keypair()

    payload = {"v": 1, "pid": "TEST-123", "iat": 123456789}

    pill = sign_payload(priv, payload)

    assert '.' in pill
    parts = pill.split('.')
    assert len(parts) == 2

    decoded = verify_pill(pub, pill)
    assert decoded == payload

def test_tampered_payload():
    priv, pub = generate_keypair()
    payload = {"v": 1, "pid": "TEST-123", "iat": 123456789}
    pill = sign_payload(priv, payload)

    parts = pill.split('.')
    # Tamper with payload part
    tampered_pill = parts[0][:-1] + 'A.' + parts[1]

    with pytest.raises(ValueError):
        verify_pill(pub, tampered_pill)

def test_tampered_signature():
    priv, pub = generate_keypair()
    payload = {"v": 1, "pid": "TEST-123", "iat": 123456789}
    pill = sign_payload(priv, payload)

    parts = pill.split('.')
    # Tamper with signature
    sig = list(parts[1])
    sig[0] = 'a' if sig[0] != 'a' else 'b'
    tampered_pill = parts[0] + '.' + "".join(sig)

    with pytest.raises(ValueError):
        verify_pill(pub, tampered_pill)
