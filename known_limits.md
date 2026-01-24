# Known Limits & Security Debt

This document outlines the intentional limitations and security shortcuts taken for the demonstration scope of the `pill_generator` project.

## 1. Hardcoded Cryptographic Roots
### Authority Keys (Issuance & Gateway)
*   **Implementation**: A fixed 32-byte seed (sequence `0..31`) is used to derive the `Ed25519` keypair in both `IssueController` and `SwapController`.
*   **Risk**: The private key is essentially public knowledge. Anyone with access to the source code can forge pills.
*   **Remediation**: Use a secure Key Management System (KMS) or mount a secret volume to load the seed/key at runtime.



## 3. NSec Key Export
*   **Implementation**: Keys are explicitly created with `KeyExportPolicies.AllowPlaintextExport` to facilitate storage in `neuer-keyless`.
*   **Risk**: If the `SubscriptionService` memory is dumped, private keys are visible.
*   **Context**: Necessary for the "Remote Key Storage" pattern where the service generates the key but offloads persistence.
