# Changelog

## Known Issues / Tribal Knowledge
*   [ ] ...

## Change History
*   **[2026-01-24] Entitlement As A Service & Keyless Integration:**
    *   **Architecture**: Documented EaaS pattern in `EntitlementAsAService.md`.
    *   **Integration**: Integrated `neuer-keyless` into `SubscriptionService` for secure private key storage.
    *   **Refactor**: Modified burn logic to generate Ed25519 keypairs upon consumption. Private key stored in Keyless, Public key in Etcd.
    *   **Infrastructure**: Updated `docker-compose.yml` to support cross-stack communication with `neuer-keyless` via host gateway.
    *   **Testing**: Added comprehensive Python E2E test suite in `tests/` covering full lifecycle, negative cases, and edge cases.
    *   **Refactor**: Updated `GatewayService` to mint JWTs via `neuer-keyless` (Centralized Crypto).
    *   **Refactor**: Updated `InternalService` to verify JWTs via `neuer-keyless` (Remote Verification).
    *   **Migration**: Validated port to .NET 8.0 for all microservices.
    *   **Security**: Removed hardcoded secrets (`JwtConstants`, `AuthorityKey`) and replaced with Environment Variables.
    *   **Feature**: Implemented **Claims Preservation** to forward `ExtensionData` from Pill to JWT.
    *   **Architecture**: Implemented **Hybrid Asymmetric Crypto** (EdDSA + HS256):
        *   Updated `neuer-keyless` to support `EdDSA` signing via `alg` claim using stored Private Keys.
        *   Updated `InternalService` to support **Local EdDSA Verification** using Public Keys fetched from `etcd`.
        *   Maintained backward compatibility with HS256 fallback.
    *   **Documentation**: Added `docs/adr/0001-centralized-cryptography-via-keyless.md`.
*   **[Date] Initialization:** Created standard documentation structure.
