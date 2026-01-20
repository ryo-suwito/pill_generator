# Distributed Pill-Based Subscription Engine

**Version:** 1.0
**Author:** Tech Lead

## Executive Summary

This project implements a **Distributed Pill-Based Subscription Engine**, a dual-domain system designed to decouple entitlement from authorization. It moves away from stateful database-driven checks towards **Cryptographic Entitlement** and **Distributed Consensus**.

The architecture consists of two main domains:
1.  **Issuance Domain**: Generates cryptographically signed bearer assets ("Pills").
2.  **Subscription Domain**: Manages the atomic lifecycle ("Burn") and stateless service-to-service authorization ("Swap").

## Architecture

### High-Level Design

*   **Issuance Service (The Factory)**: Signs batches of Pills using Ed25519. It maintains a Shadow DB for inventory but is not involved in validation.
*   **Subscription Service (The Truth Engine)**: A gRPC service backed by **etcd**. It enforces Anti-Double Spend logic using Atomic CAS (Compare-And-Swap) transactions.
*   **Gateway Service**: The entry point for clients. It performs the "Swap" operation: verifying the Pill's signature, calling the Subscription Service to burn it, and issuing a short-lived **Internal JWT**.
*   **Internal Service**: Represents downstream microservices. They validate the Internal JWT locally (stateless) using the Gateway's public key.

### Data Flow

1.  **Issue**: `POST /issue` -> Returns a signed Pill (Base64 payload + Hex Signature).
2.  **Swap**: `POST /swap` -> Client presents Pill. Gateway verifies signature -> Calls Subscription Service to Burn (Atomic Check) -> Returns Internal JWT.
3.  **Access**: `GET /data` -> Client presents Internal JWT. Internal Service verifies JWT -> Grants Access.

## Prerequisites

*   **Docker** and **Docker Compose**
*   **Python 3.12+** (for local development/testing)

## Installation & Running

The entire stack is containerized. To start the system:

```bash
docker-compose up --build
```

This will spin up:
*   `etcd` (Port 2379)
*   `issuance-service` (Port 8000)
*   `gateway-service` (Port 8001)
*   `internal-service` (Port 8002)
*   `subscription-service` (Port 50051 - gRPC)

## Usage

### 1. Issue a Pill
Generate a new signed pill.

```bash
curl -X POST http://localhost:8000/issue \
  -H "Content-Type: application/json" \
  -d '{"pid": "BATCH-001-ID-123", "iat": 1737400000}'
```

**Response:**
```json
{
  "pill": "ey...signed_content..."
}
```

### 2. Swap Pill for Token
Exchange the Pill for an access token. This burns the pill, ensuring it cannot be used again.

```bash
curl -X POST http://localhost:8001/swap \
  -H "Content-Type: application/json" \
  -d '{"pill": "<YOUR_PILL_STRING>"}'
```

**Response:**
```json
{
  "token": "eyJhbGciOi...",
  "expires_in": 300
}
```

### 3. Access Protected Resource
Use the token to access internal services.

```bash
curl -X GET http://localhost:8002/data \
  -H "Authorization: Bearer <YOUR_TOKEN>"
```

**Response:**
```json
{
  "message": "Access granted",
  "user_id": "BATCH-001-ID-123",
  "service": "Internal Service A"
}
```

## Development

### Project Structure

*   `common/`: Shared libraries for Crypto (Ed25519) and Pydantic Models.
*   `issuance_service/`: FastAPI app for issuing pills.
*   `subscription_service/`: gRPC service for burning pills (etcd interaction).
*   `gateway_service/`: FastAPI app for the Swap logic.
*   `internal_service/`: Example protected service.
*   `proto/`: Protobuf definitions.

### Running Tests

Install dependencies:

```bash
pip install -r requirements.txt
pip install cryptography  # Required for JWT RS256 tests
```

Run unit tests:

```bash
export PYTHONPATH=$PYTHONPATH:.
pytest common/test_crypto.py \
       issuance_service/test_issuance.py \
       subscription_service/test_subscription.py \
       gateway_service/test_gateway.py \
       internal_service/test_internal.py
```

## Guarantees

*   **Security**: Impossible to forge pills without the Private Key (Ed25519).
*   **Integrity**: Impossible to double-spend a pill due to Raft consensus (etcd).
*   **Scalability**: Subscription checks are O(1) local math operations for internal services; Consensus check is only performed once per session (at Swap).
