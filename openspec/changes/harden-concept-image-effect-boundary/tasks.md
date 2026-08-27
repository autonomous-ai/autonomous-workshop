> **Priority: Low — deferred backlog.** Do not treat these tasks as blockers for
> the current native-runtime migration. Begin only when this change is
> explicitly selected for implementation.

## 1. Characterize the unsafe boundary

- [ ] 1.1 Add failure-path characterization tests for interruption before send, after provider acceptance, after response receipt, and after image write; verify the current duplicate-risk windows are reproduced without making live provider calls.
- [ ] 1.2 Inventory supported provider transports for stable idempotency and authenticated operation lookup, and verify each paid transport is classified as safely supported or refused before transmission.

## 2. Durable effect records and authorization

- [ ] 2.1 Define versioned contracts for image-effect intent, attempt, reconciliation, receipt, and `unknown-outcome`; verify canonical round-trips and refusal of missing or mismatched identity fields.
- [ ] 2.2 Persist the complete immutable intent and stable idempotency key atomically before send; verify crash-before-send resumes the same unperformed intent without creating another identity.
- [ ] 2.3 Add durable transmission authorization bound to run, checkpoint, subject, provider origin, operation, instruction hash, and reference hashes; verify configured credentials alone never authorize or transmit private inputs.
- [ ] 2.4 Surface missing or stale authorization as a durable waiting need; verify status names the need without exposing Wish text, reference bytes, credentials, or sensitive provider data.

## 3. Safe provider execution and reconciliation

- [ ] 3.1 Extend the provider transport boundary with stable idempotency and authenticated result-readback operations; verify transports supporting neither are rejected before any paid call.
- [ ] 3.2 Route every Concept image role through the host effect ledger and reuse its persisted key on safe resend; verify repeated execution of one logical request cannot create a second intent.
- [ ] 3.3 Persist the provider operation identifier and attempt state at the earliest safe point; verify a lost response produces `unknown-outcome` rather than an automatic retry.
- [ ] 3.4 Implement authenticated reconciliation for completed, not-accepted, still-running, and unresolved results; verify each result produces the specified receipt, safe same-key retry, continued wait, or unknown state.
- [ ] 3.5 Bind verified receipts to exact returned-byte hashes and provider evidence; verify altered bytes, substituted operation identifiers, stale subjects, and unreceipted files fail closed.

## 4. Gate and lifecycle separation

- [ ] 4.1 Split pre-effect structural validation, effect execution or reconciliation, and final Concept gate evaluation; verify gate evaluation performs no network or credential-bearing call.
- [ ] 4.2 Require one matching verified receipt for every declared image role before sealing and advancing; verify partial sets and any `unknown-outcome` remain parked.
- [ ] 4.3 Replace file-presence skipping and inline retry behavior with ledger-derived recovery; verify missing files do not imply safe resend and existing unreceipted files do not imply success.
- [ ] 4.4 Define migration handling for in-flight runs and verify runs with no attempted effect resume safely while unreceipted or ambiguous effects park for reconciliation or restart.

## 5. Acceptance and documentation

- [ ] 5.1 Add deterministic end-to-end tests covering duplicate suppression, authenticated readback recovery, indefinite unknown outcome, authorization refusal, and same-session continuation; verify no test performs a live paid effect.
- [ ] 5.2 Add architecture tests proving only the trusted host can create effect intents, use provider credentials, reconcile results, and write receipts; verify native sessions and gates cannot access those capabilities.
- [ ] 5.3 Document the authorization, receipt, reconciliation, and operator recovery model, explicitly stating that receipts prove external execution only; verify terminology matches the public contracts and status output.
- [ ] 5.4 Run the full offline gate set, secret scan, packaging acceptance, and `git diff --check`; verify all pass before this backlog change is considered implemented.
