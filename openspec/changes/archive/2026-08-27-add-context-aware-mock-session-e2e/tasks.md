## 1. Acceptance Contract and Isolation

- [x] 1.1 Add the explicit live-Codex test marker, opt-in configuration, and skip/preflight behavior; verify the default unit and deterministic E2E commands do not select the mock-session scenario and missing/unsupported Codex exits with a clear prerequisite result.
- [x] 1.2 Define and validate the bounded per-stage context-record schema, including checkpoint/subject bindings, consulted instruction hashes, used input keys and paths, fixture strategy, output hashes, and deferred work; verify malformed, stale, missing, and oversized records fail focused tests.
- [x] 1.3 Add an architecture guard that prevents normal CLI/product-run paths from selecting mock-session behavior or importing test helpers; verify representative environment flags and production commands cannot activate the mode.

## 2. Real Codex Pass-Through

- [x] 2.1 Implement the test-only pass-through executable that delegates version and start/resume execution to the real Codex binary while appending only the versioned generic minimal-work directive; verify argument, JSONL event, exit-status, and signal forwarding and assert the directive contains no stage-specific schemas, commands, ownership rules, or transitions.
- [x] 2.2 Exercise the pass-through with the production native launcher for a start/resume smoke run; verify a real session checkpoint is created, the same session identity is resumed, the recorded runtime configuration matches the actual model/effort, and no scripted or in-process agent result is used.
- [x] 2.3 Add prohibited-activity observations for native web search, non-loopback network attempts, unnecessary spawned agent work where observable, and credential exposure; verify each detectable violation fails with the current stage in diagnostics.

## 3. Isolated Local Effect Fixtures

- [x] 3.1 Implement a loopback-only deterministic Concept image-provider protocol server using existing transport contract fixtures; verify the production Concept adapter performs request validation, ordered image writes, and sealing while the fixture writes no run artifacts.
- [x] 3.2 Implement a loopback-only deterministic Factory protocol server for private import and authenticated readback; verify the production credential parser, release writer, effect ledger, idempotency, reconciliation, and receipt validation remain active.
- [x] 3.3 Add fixture-secret and write-ownership audits spanning process environments, prompts, workspace files, context records, host state, and protocol-server writes; verify seeded secrets never reach Codex and deliberate host-owned writes by a helper are rejected.

## 4. Context-Aware Full Pipeline Scenario

- [x] 4.1 Add the isolated runner, fixed simple Wish, temporary Workshop home, local service lifecycle, per-turn budget, whole-run budget, redaction, and retained-failure-workspace behavior; verify clean startup/shutdown, timeout termination, and nonzero failure statuses.
- [x] 4.2 Drive real Codex through Match and Invent using normal materialized instructions; verify stage context records bind the actual instruction/input bytes, production finalizers and gates run, and the same native session resumes.
- [x] 4.3 Drive real Codex through the pre-render Concept boundary and host rendering; verify the session finalizes before image paths or sealed Concept exist, then the production host creates and seals them through the local provider protocol.
- [x] 4.4 Drive real Codex through minimal Make and Playtest; verify the chosen outputs are derived from the accepted Wish/Invent/Concept inputs, the production CAD verifier runs on exact artifact bytes in both gates, and all universal checks are represented without fabricated host evidence.
- [x] 4.5 Drive real Codex through Release to private Deliver; verify the production finalizer, factual-evidence bindings, local Factory import/reconciliation, sealed Release, checkpoint transitions, one start plus subsequent resumes, and final private Deliver wait.

## 5. Fidelity Failures and Diagnostics

- [x] 5.1 Add mutation scenarios that remove or corrupt a materialized skill description, referenced resource, `STAGE.json` input, and upstream artifact; verify the run fails at the affected stage without the generic directive supplying the missing production rule.
- [x] 5.2 Add context-record failure scenarios for invented paths, wrong hashes, stale checkpoint/subject values, unrelated input keys, and output inventories that disagree with the finalizer proposal; verify each is rejected even when the stage contract is otherwise structurally valid.
- [x] 5.3 Add boundary regression coverage reproducing the former Concept finalization/image-generation cycle; verify the corrected production instructions succeed and a deliberately regressed instruction fails before the host waits indefinitely.
- [x] 5.4 Emit a concise success/failure report with model, effort, session start/resume counts, stage trace, per-stage duration, context-proof result, final checkpoint, total duration, and redacted diagnostic location; verify stable fields in automated tests without asserting exact model prose, tokens, or timing.

## 6. Local Command and Documentation

- [x] 6.1 Add one documented contributor command for the opt-in mock-session E2E run, including authentication, supported Codex version, expected local services, budgets, diagnostic cleanup, and troubleshooting; verify the command reaches the test preflight from a clean checkout.
- [x] 6.2 Document the three verification tiers—offline deterministic E2E, real-Codex mock-session acceptance, and full product run—and their evidence limits; verify no documentation presents mock-session success as product quality, remote publication, manufacture, printing, delivery, or human-response evidence.
- [x] 6.3 Run the focused unit/integration tests, offline deterministic E2E suite, OpenSpec strict validation, and one measured real-Codex mock-session run; record the observed stage trace and elapsed time in the implementation handoff and verify all tiers pass independently.
