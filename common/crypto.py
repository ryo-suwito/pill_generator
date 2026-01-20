
import nacl.signing
import nacl.encoding
import base64
import json
from typing import Tuple

def generate_keypair() -> Tuple[str, str]:
    """
    Generates a new Ed25519 keypair.
    Returns: (private_key_hex, public_key_hex)
    """
    signing_key = nacl.signing.SigningKey.generate()
    verify_key = signing_key.verify_key

    private_key_hex = signing_key.encode(encoder=nacl.encoding.HexEncoder).decode('utf-8')
    public_key_hex = verify_key.encode(encoder=nacl.encoding.HexEncoder).decode('utf-8')

    return private_key_hex, public_key_hex

def sign_payload(private_key_hex: str, payload: dict) -> str:
    """
    Signs a dictionary payload using the private key.
    Pill Structure: Base64(Payload) . Hex(Signature)
    """
    payload_json = json.dumps(payload, separators=(',', ':'))
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode('utf-8')).decode('utf-8').rstrip('=')

    signing_key = nacl.signing.SigningKey(private_key_hex, encoder=nacl.encoding.HexEncoder)

    # We sign the Base64 payload string
    # Actually, usually you sign the raw bytes or the standardized string.
    # The requirement says: Pill Structure: Base64(Payload) . Hex(Signature)
    # It doesn't explicitly say what is signed, but usually it's the Base64 part or the raw JSON.
    # JWT signs `Header.Payload`.
    # Here, "Pill Structure: Base64(Payload) . Hex(Signature)" implies Signature covers Base64(Payload)
    # OR it's just a concatenation.
    # Let's assume we sign the Base64 string of the payload to be safe and consistent with JWT-like structures.

    signature_bytes = signing_key.sign(payload_b64.encode('utf-8')).signature
    signature_hex = signature_bytes.hex()

    return f"{payload_b64}.{signature_hex}"

def verify_pill(public_key_hex: str, pill: str) -> dict:
    """
    Verifies the pill string.
    Returns the payload dict if valid, raises exception otherwise.
    """
    try:
        payload_b64, signature_hex = pill.split('.')
    except ValueError:
        raise ValueError("Invalid pill format")

    verify_key = nacl.signing.VerifyKey(public_key_hex, encoder=nacl.encoding.HexEncoder)

    try:
        signature_bytes = bytes.fromhex(signature_hex)
        verify_key.verify(payload_b64.encode('utf-8'), signature_bytes)
    except Exception as e:
        raise ValueError(f"Signature verification failed: {e}")

    # Decode payload
    try:
        # Add padding back if necessary
        padding = '=' * (-len(payload_b64) % 4)
        payload_json = base64.urlsafe_b64decode(payload_b64 + padding).decode('utf-8')
        return json.loads(payload_json)
    except Exception as e:
        raise ValueError(f"Payload decoding failed: {e}")
