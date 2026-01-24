# Product Requirements

## Overview
The `pill_generator` is a distributed subscription engine that issues cryptographic "Pills" (entitlements) and manages their lifecycle (redemption/burning) to prevent double-spending. It issues JWTs for session management upon successful pill redemption.

**Constraint:** The entire system must be implemented within the **.NET Ecosystem** (C# / ASP.NET Core), replacing the previous Python/FastAPI implementation.

## Core Functionality

### 1. Pill Issuance
*   **Authority:** The system must act as a central authority to issue new entitlements.
*   **Cryptography:** Pills must be signed using **Ed25519** to ensure authenticity and non-repudiation.
*   **Payload:** Pills should contain unique identifiers (`pid`) and issuance timestamps (`iat`).
*   **Output:** The API returns a serialized, signed pill string (e.g., `Base64Payload.HexSignature`).

### 2. Pill Redemption (Gateway)
*   **Entry Point:** Provide a public API (`/swap`) for clients to exchange a Pill for an access token.
*   **Validation:**
    *   Verify the Ed25519 signature of the Pill.
    *   Verify the Pill has not been used ("burnt") previously.
*   **Session Issuance:** Upon successful validation and burning, issue a **JWT (JSON Web Token)** signed with RSA (or appropriate algorithm).
    *   Token lifespan: Short (e.g., 5 minutes).

### 3. Subscription Lifecycle (Double-Spend Protection)
*   **State Management:** Maintain the state of spent pills to prevent replay attacks (Double Spending).
*   **Consistency:** Use a distributed store (originally `etcd`) to enforce atomic "burn" operations.
*   **Interface:** Provide an internal interface (gRPC or HTTP) for the Gateway to request pill burning.

### 4. Protected Resources (Internal Service)
*   **Access Control:** Validate the Internal JWT issued by the Gateway.
*   **Resource Access:** Allow access to protected data only with a valid, unexpired token.

## Technical Stack Constraints
*   **Language:** C# (.NET 8.0 or later)
*   **Framework:** ASP.NET Core
*   **Communication:** gRPC (for internal Subscription service), HTTP/REST (for public APIs).
*   **Storage:** `etcd` (via standard .NET client) for distributed consensus/state.
*   **Containerization:** Docker & Docker Compose support.

## API Surface

### Issuance Service
*   `POST /issue`: Generate a new signed pill.

### Gateway Service
*   `POST /swap`: Exchange a pill for a JWT.

### Internal Service
*   `GET /data`: Access protected data (Requires Bearer Token).
