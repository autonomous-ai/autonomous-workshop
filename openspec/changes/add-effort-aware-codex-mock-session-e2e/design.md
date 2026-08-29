## Context

See `proposal.md` for motivation and `specs/workshop/effort-aware-codex-mock-session-e2e/spec.md` for the observable contract.

Current `main` already has the required offline production-boundary E2E. It replaces only Codex at `WORKSHOP_CODEX_BIN` and Factory's outbound transports, then exercises Spark, Forge, and Quest through production finalizers and gates. The missing layer is model/context acceptance: whether a real authenticated Codex session can understand the immutable product-run assets and current stage packets. The historical implementation in `feat/concept-phase` established a useful pass-through wrapper, context-record schema, bounded runner, protocol fixture, and ownership/security audits, but its route was Match -> Invent -> Concept -> Make -> Playtest -> private Deliver. None of those obsolete topology assumptions can remain.

The new tier must stay subordinate to ADR 0012 and ADR 0016. Codex owns cognition and tool use inside one persistent session; the host owns lifecycle state, gates, exact-byte evidence, credentials, and effects. Terminal success is published Release under ADR 0014, with truthful Playtest omission for Spark and Forge.

## Goals / Non-Goals

**Goals:**

- Reuse the source branch's proven test architecture where it remains compatible, while deriving route assertions from the current effort contract.
- Catch regressions in instruction discovery, packet interpretation, cross-stage context, finalizer use, and native start/resume continuity.
- Retain production verification and publication code while keeping every remote response deterministic and local.
- Produce failures that identify the route, stage, context binding, ownership boundary, or prohibited activity that drifted.

**Non-Goals:**

- Evaluate creative quality, research depth, complex CAD, manual aesthetics, or physical behavior.
- Exercise Concept contracts, rendering, or effects before Concept is activated by a later architecture decision.
- Add a test mode to the production CLI or product-run constitution.
- Duplicate QA-1's exhaustive deterministic repair, tamper, ambiguity, and wait/resume matrix with expensive live model calls.
- Make a credentialed nondeterministic job a required pull-request gate.

## Decisions

### 1. Port the historical harness as test-only code, not its production topology changes

The acceptance implementation will adapt the historical files into focused modules under `tests/end_to_end/` plus one `tools/` entry point. It will reuse current production `start_native_run`/`resume_native_run`, `CodexNativeSessionLauncher`, materialized assets, finalizer, workflow gates, and the existing outbound Factory transport seams. The harness will not introduce a stage agent, a second transition table, or mock behavior reachable from `workshop wish`.

An architecture/policy test will reject imports of mock-session helpers from `src/`, `src/cli/`, or `.agents/product-run/`, and will restrict internal replacements in the live scenario to the same external boundaries approved for deterministic E2E: the Codex executable and Factory outbound transports.

**Alternative considered:** transplant commit `1853cfd` and patch stage names afterward. Rejected because its Concept pre-render server, standalone Match assertions, private Deliver result, and older release payload would preserve obsolete assumptions in otherwise plausible code.

### 2. Use a transparent pass-through executable to add one generic acceptance overlay

The runner will resolve the contributor's real Codex binary, then set `WORKSHOP_CODEX_BIN` to a test-only wrapper. The wrapper will delegate version checks and all native start/resume arguments to the real binary, forward stdin/stdout/stderr, exit status, and termination signals, and preserve the production JSONL protocol. It will append a bounded, versioned directive that says to:

- read the normal constitution, applicable skills, current `STAGE.json`, and upstream inputs;
- perform the smallest valid context-derived work;
- write the generic test context record;
- avoid web, live services, credential requests, and unnecessary subagents;
- invoke the normal finalizer and return.

The directive will describe only its route-independent context-record format. It will contain no stage names beyond the value read from `STAGE.json`, no artifact schemas, finalizer subcommands, transition targets, folded-selection rules, or omission rules. Static tests will scan it for forbidden workflow knowledge and verify byte-for-byte argument/event forwarding with a fake child; the actual acceptance scenario will require the resolved real Codex binary and a native session checkpoint.

**Alternative considered:** add a mock skill with exact output recipes. Rejected because it could pass while the production skill or stage packet is unusable—the regression class this test exists to detect.

### 3. Validate model-authored context records against turn-time and final bytes

For each native turn, the wrapper will snapshot the current run-root `STAGE.json`, checkpoint and subject digests, immutable instruction identities, native event summary, and the hashes of files named by the model-authored context record. The bounded record will live under a test-only `.mock-session/` path and contain:

- stage, checkpoint, subject, and stage-packet digest;
- consulted run-relative instruction paths and SHA-256 values;
- used input keys plus any run-relative artifact paths and hashes;
- one bounded strategy identifier and explanation;
- agent-owned output paths and SHA-256 values;
- explicitly deferred expensive work.

After the host processes the proposal, the harness will compare the record with the captured packet, finalizer proposal inventory, accepted artifact manifests, and final source bytes. It will resolve all paths strictly beneath the run root and reject checkout paths, harness fixtures, symlinks, stale checkpoints, intermediate hashes, and files absent from the relevant packet. This carries forward the intent of `69afa5c` (final source bytes) and `e4eb604` (run-root bindings only).

The record proves byte discovery and linkage, not the truth of the model's explanation. Stage-appropriate success is established by the normal finalizer and host gates.

**Alternative considered:** treat a successful finalizer as sufficient evidence of context use. Rejected because a static lucky fixture can finalize without revealing that an upstream input or instruction was ignored.

### 4. Run an explicit effort route, and schedule the complete route matrix

The local entry point will require or default an explicit `--effort` value and execute one fresh fixed Wish per invocation. Route expectations come from the frozen current effort definition and are cross-checked against QA-1's authoritative topology constants rather than restated in the overlay:

| Effort | Expected real-Codex turns | Selection and Playtest behavior |
|---|---|---|
| Spark | Make -> Release | Make folds assignment and Invented; Release records `not-run` |
| Forge | Invent -> Make -> Release | Invent folds assignment; Release records `not-run` |
| Quest | Invent -> Make -> Playtest -> Release | Invent folds assignment; Release binds passing Playtest |

The scheduled/manual workflow will run a three-entry matrix so every current route gets model/context acceptance. Each Wish gets its own persistent session; session identity is never shared across routes. The local command may run a single selected route for faster diagnosis. Route reports remain independent so one failure does not hide the others.

The fixed Wish will deliberately admit simple valid geometry and a concise manual, but it will remain ordinary product intent rather than a hidden stage recipe. Codex must use production Make and Release resources to create valid bytes.

**Alternative considered:** cover Forge only because it is the middle route. Rejected because Spark's compound Make proposal and Quest's active Playtest have different materialized context and finalizer contracts.

### 5. Keep host-owned Factory publication real behind a loopback protocol fixture

Concept image infrastructure from the old harness will be removed. A loopback-only Factory fixture will implement the minimum import, metadata, publish, authenticated readback, and public file-read responses required by current Release. The harness will inject it only through the existing production outbound transport seams. Production credential parsing, release writer, durable intent/idempotency ledger, reconciliation, receipt validation, public transition, and exact CAD/manual/page readback will remain active.

The fixture will keep an operation log and reject unexpected methods, paths, missing authentication, duplicate non-idempotent operations, byte mismatches, and any non-loopback remapping. Its project-file response will return the exact sealed manual bytes it received so production hash verification remains meaningful. It will not write inside the run workspace or host-state root.

Fixture credentials will exist only in the host test process. The production native environment scrubber must remove them before launching the wrapper and real Codex. The harness will seed recognizable canary secrets and scan prompts, captured native environments, agent-readable files, context records, reports, and retained diagnostics.

**Alternative considered:** patch the Release evaluator or Factory writer. Rejected because that would bypass the effect ordering, ownership, reconciliation, and terminal-state behavior under test.

### 6. Separate offline harness verification from live acceptance

Ordinary unit tests will exercise context-record parsing, final-byte rebinding, run-root restrictions, wrapper forwarding, event classification, secret redaction, topology assertions, write inventories, preflight failures, timeout cleanup, loopback protocol behavior, and report labeling with deterministic children. These tests validate the harness itself but will not claim live-Codex acceptance.

The live test module will be skipped unless an explicit environment switch is present and preflight confirms a supported version and usable authentication. The tool entry point will create a private temporary Workshop home, run the selected route in a bounded worker process, and delete it after success unless `--keep` is requested. Failure and timeout retain a redacted diagnostic manifest and exact local paths for inspection.

Per-turn limits are enforced by the production launcher configuration used for that run; the outer worker provides an independent whole-route ceiling and terminates only the process tree it created. Reports use bounds, not brittle exact token or duration assertions.

**Alternative considered:** add real Codex directly to the deterministic E2E job. Rejected because it would make required CI authenticated and nondeterministic while weakening the distinct offline guarantee.

### 7. Add a separate non-required manual/scheduled workflow

A dedicated workflow, separate from `.github/workflows/ci.yml`, will expose manual dispatch and a schedule. It will target the repository's configured credentialed runner/environment and execute a Spark/Forge/Quest matrix using the documented tool command. No credential value will be committed, echoed, placed in the run workspace, or forwarded through the native environment. Each matrix result will upload only the bounded redacted report; retained workspaces stay on the controlled runner and are not uploaded automatically.

The workflow's exact runner label and authentication provisioning remain deployment configuration, not an application contract. If no credentialed runner is configured, the job must fail preflight or remain disabled rather than silently substitute deterministic Codex.

**Alternative considered:** add the matrix to the required push/pull-request workflow. Rejected because forks and normal CI must remain credential-free, and model availability is not deterministic enough for a merge gate.

### 8. Temporarily fail open after exact finalization when Codex omits its terminal event

Initial authenticated characterization suggested that Codex could atomically write the exact `agent-outcome.json`, finish its Goal, and omit or delay `turn.completed` beyond the launcher's bounded marker grace. Deeper comparison of the retained Forge and Quest rollouts did not reproduce that behavior: every actual turn completed, neither used subagents, and the Quest retry failure was a test-wrapper snapshot collision before Codex launched. The compatibility path remains temporarily while the suspected runtime behavior receives an isolated reproduction, but it is not presented as established upstream causality.

This marker remains liveness-only. The workflow host still parses the proposal, verifies checkpoint and subject bindings, rehashes artifacts, runs deterministic gates, and rejects malformed, stale, or invalid output. Unsafe process cleanup, invalid identity, malformed events, and explicit failures remain fail-closed. The compromise and its removal criteria are recorded in `docs/backlog/codex-missing-turn-completed-after-subagents.md`.

If the missing terminal leaves no proposal, the launcher classifies only a cleanly reaped invocation that observed the valid native thread identity as recoverable. The workflow may continue solely by resuming an already checkpointed exact session under the unchanged checkpoint, subject, Goal, mutation lock, and native-turn ceiling; pre-identity wrapper and preflight failures remain fail-closed.

The acceptance wrapper snapshots each exact packet by checkpoint plus subject because deterministic same-stage repair feedback intentionally changes the subject without advancing the lifecycle checkpoint. Marker mutation and scripted extra resume calls remain rejected because they would bypass or distort the production launcher boundary the live tier exists to exercise.

## Risks / Trade-offs

- **[Risk] Nine real turns across the full matrix remain slow and model-variable.** -> Keep local runs route-selectable, use a simple Wish and low-cost valid outputs, schedule the matrix outside pull requests, and optimize production instruction clarity rather than bypassing it.
- **[Risk] The generic overlay can accidentally become a second workflow specification.** -> Version and statically audit it; prohibit stage schemas, commands, routes, and ownership recipes; require production-instruction hashes in every context record.
- **[Risk] Model-authored context explanations can be plausible but false.** -> Trust only independently checked paths, packet membership, digests, final source bytes, accepted manifests, and production gate results; label semantic inference narrowly.
- **[Risk] A wrapper can alter native protocol behavior.** -> Test exact argument/event/status/signal forwarding, preserve real session identifiers, and require the production session checkpoint to bind the actual model and effort.
- **[Risk] The loopback Factory fixture can drift from production transport contracts.** -> Reuse current integration-test response builders where possible, assert all calls and exact returned bytes, and keep live Factory conformance outside this acceptance claim.
- **[Risk] Credentialed scheduled infrastructure may be unavailable or compromised.** -> Keep scheduling non-required, use an isolated least-privilege runner/environment, run preflight before creating state, and never upload raw workspaces or credentials.
- **[Risk] Test helpers could become a production shortcut.** -> Keep them outside distributable source, add dependency/static-policy guards, and make activation possible only through the test tool and explicit environment switch.

## Migration Plan

1. Port and update the context record, pass-through wrapper, bounded worker, redaction, and policy tests without enabling a live run.
2. Add the current Factory loopback protocol and exact publication/readback assertions.
3. Implement Spark live acceptance first because its two-turn path validates compound Make selection and terminal Release with the smallest runtime.
4. Add Forge and Quest using the same harness, then enforce route absence/ordering and per-route session continuity.
5. Document the local command and evidence limits; add the separate manual/scheduled route matrix only after all offline harness tests pass.
6. Run the complete live matrix once on a controlled authenticated environment and record only sanitized timing and pass/fail evidence.

Rollback removes the test-only runner, wrapper, fixtures, live workflow, and documentation. It does not rewrite run formats, product-run assets, production lifecycle state, or historical evidence.
