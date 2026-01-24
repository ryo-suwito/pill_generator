# 1. Centralized Cryptography via Keyless

Date: 2026-01-24

## Status

Accepted

## Context

The initial implementation of `pill_generator` relied on decentralized, local cryptographic operations:
1.  **Local Secrets**: Hardcoded seeds/keys were present in `IssueController` and `SwapController`.
2.  **Symmetric Signing**: JWTs were signed locally using a shared secret constant (`JwtConstants`).
3.  **Fragmented State**: Keys were managed implicitly by the service instance, making rotation and revocation difficult.

To move towards a production-ready "Entitlement as a Service" (EaaS) architecture, we needed to separate the concerns of *Policy* (Issuance/Gateway) from *Mechanism* (Key Management).

## Decision

We will centralize all cryptographic operations (Key Generation, Storage, Signing, and Verification) into the `neuer-keyless` service.

We adopt the **EaaS Pattern** where:
*   The **Pill** represents the *Entitlement*.
*   The **Key** represents the *Access Capability*.
*   The transition from Entitlement to Access (The "Burn") generates the Key on-demand.

### Specific Changes
1.  **Subscription Service**:
    *   Generates a fresh Ed25519 Keypair *specifically* for the burnt pill.
    *   **Private Key**: Sent immediately to `neuer-keyless`. Never persisted to local disk.
    *   **Public Key**: Stored in `etcd` as proof of burn/existence.

2.  **Gateway Service**:
    *   Delegates JWT Minting ('Recipe to Wristband') to `neuer-keyless`.
    *   Forwards all `ExtensionData` from the Pill to the JWT claims ("Claims Preservation").

3.  **Internal Service**:
    *   **EdDSA (Preferred)**: Fetches the **Public Key** from `etcd` (using the pill ID) and verifies the signature locally. This treats `etcd` as the Distributed PKI.
    *   **HS256 (Legacy)**: Falls back to delegating verification to `neuer-keyless` via RPC if `alg` is not EdDSA.
    *   Eliminates the need for shared secrets between Gateway and Internal services for the primary flow.

## Consequences

### Positive
*   **Security hardening**: Private keys are isolated in a dedicated vault (`neuer-keyless`). No hardcoded secrets remain in the application code.
*   **Auditability**: A centralized log of all mint/verify operations is available in Keyless.
*   **Agility**: Key rotation and algorithm changes can be managed in Keyless without redeploying the application services.
*   **Contract Preservation**: Arbitrary payload data is securely carried over from the "Recipe" (Pill) to the "Wristband" (Token) without the Gateway needing to understand the schema.

### Negative
*   **Operational Complexity**: The `pill_generator` stack now has a hard dependency on `neuer-keyless` being available.
*   **Latency**: Mint and Verify operations now incur an extra network hop (gRPC), compared to in-memory verification.
