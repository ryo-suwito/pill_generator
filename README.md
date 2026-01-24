# Distributed Pill-Based Subscription Engine

A microservices-based system demonstrating a distributed subscription mechanism using cryptographic assets ("Pills") and consensus-based lifecycle management.

## Overview

This project implements a subscription engine where access rights are represented by signed bearer tokens called "Pills". These pills are issued by an authority and can be redeemed ("burnt") for short-lived access tokens (JWTs) via a Gateway. The system ensures double-spending protection using distributed consensus (etcd).

## Architecture

The system consists of the following microservices:

*   **Issuance Service**: Responsible for generating cryptographically signed pills using Ed25519. It acts as the authority for creating assets.
*   **Subscription Service**: Manages the lifecycle of pills. It uses `etcd` to enforce single-use properties (burning pills) through atomic transactions to prevent double-spending. Exposes a gRPC interface.
*   **Gateway Service**: The entry point for clients. It orchestrates the validation of pills (verifying signatures) and redemption (calling the Subscription Service to burn them). Upon success, it issues an internal JWT for access to protected resources.
*   **Internal Service**: A sample protected resource that requires a valid internal JWT issued by the Gateway.
*   **etcd**: A distributed key-value store used for consensus and tracking burnt pills.

## Technology Stack

*   **Language**: C# (.NET 8.0)
*   **Framework**: ASP.NET Core
*   **RPC Framework**: gRPC
*   **Consensus/Storage**: etcd
*   **Cryptography**: Ed25519 (NSec.Cryptography)
*   **Containerization**: Docker, Docker Compose

## Prerequisites

*   Docker
*   Docker Compose

## Getting Started

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd pill_generator
    ```

2.  **Start the services:**
    ```bash
    docker-compose up --build
    ```

    This will start all services and the etcd instance.

## Usage

### 1. Issue a Pill

Generate a new signed pill.

**Request:**
```bash
curl -X POST "http://localhost:8000/Issue" \
     -H "Content-Type: application/json" \
     -d '{"pid": "unique_pill_id_123", "iat": 1715000000}'
```

**Response:**
```json
{
  "pill": "Base64Payload.HexSignature"
}
```

### 2. Swap Pill for Access Token

Redeem the pill to get an internal JWT. This will burn the pill, preventing it from being used again.

**Request:**
```bash
curl -X POST "http://localhost:8001/Swap" \
     -H "Content-Type: application/json" \
     -d '{"pill": "<YOUR_PILL_STRING>"}'
```

**Response:**
```json
{
  "token": "eyJhbGciOiJSUzI1NiIs...",
  "expiresIn": 300,
  "claims": {
      "sub": "unique_pill_id_123",
      "iss": "PillGateway",
      "pid": "unique_pill_id_123",
      "access_level": "vip"
  }
}
```

### 3. Attempt Double Spend

Try to swap the same pill again.

**Response:**
```json
{
  "detail": "Burn failed: Double spend detected"
}
```

### 4. Access Protected Resource

Use the token obtained from the swap to access the internal service.

**Request:**
```bash
curl -X GET "http://localhost:8002/Data" \
     -H "Authorization: Bearer <YOUR_TOKEN>"
```

**Response:**
```json
{
    "message": "Access granted",
    "user_id": "unique_pill_id_123",
    "service": "Internal Service A"
}
```

## Development

### Project Structure

*   `Common/`: Shared libraries for cryptography, data models, and gRPC protos.
*   `GatewayService/`: ASP.NET Core Web API for the Gateway.
*   `InternalService/`: ASP.NET Core Web API for the Internal Service.
*   `IssuanceService/`: ASP.NET Core Web API for issuing pills.
*   `SubscriptionService/`: gRPC Service for pill lifecycle management.
*   `docker-compose.yml`: Service orchestration configuration.
