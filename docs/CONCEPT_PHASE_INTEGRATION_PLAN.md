# Concept Phase Incremental Integration Plan

- Status: Adopted integration plan
- Recorded: 2026-08-27
- Target: `main`
- Source: `feat/concept-phase`

> Lifecycle note: ADR 0016 defines three selectable routes for new runs. Spark
> is `Wish -> Make -> Release`, Forge is
> `Wish -> Invent -> Make -> Release` (the default), and Quest is
> `Wish -> Invent -> Make -> Playtest -> Release`. New runs have no separate
> Match turn; Inventor selection is part of the first active creative stage.
> Concept sequences below are future integration sketches and must be adapted
> to these effort routes before activation.

## Goal

Integrate the useful work from `feat/concept-phase` into a continuously moving
`main` through small, independently verifiable changes. Establish the
deterministic and real-Codex acceptance layers first so every subsequent
feature changes production behavior and its quality proof together.

The source branch is reference material, not a branch to merge wholesale. Its
commits were built against an older lifecycle in which Concept was active and
private Deliver was terminal. Current `main` bypasses Concept, has newer native
runtime and Factory behavior, and treats published Release as terminal.

## Integration strategy

```text
current main
    |
    +-- QA-1: deterministic E2E fidelity (required CI)
    |
    +-- QA-2: real-Codex mock-session acceptance (operator-run)
    |
    `-- incremental production changes
            +-- runtime fixes
            +-- Make and Factory fixes
            +-- dormant Concept contracts and gates
            +-- pre-render Concept protocol
            +-- durable Concept image effects
            `-- Concept lifecycle activation
```

Each integration change starts from the latest `origin/main`, carries its own
focused failure-path tests, and merges before the next dependent change is
rebased. Do not grow another long-lived integration branch.

## Phase 1: Merge the QA foundation

### QA-1: Deterministic E2E fidelity

Port the `enforce-deterministic-e2e-fidelity` work onto current `main` and make
it a required offline CI gate. Before Concept is restored, it must describe and
verify every lifecycle that actually exists on `main`:

```text
Spark: Wish -> Make -> terminal Release
Forge: Wish -> Invent -> Make -> terminal Release
Quest: Wish -> Invent -> Make <-> Playtest -> terminal Release
```

The deterministic suite must exercise:

- the production `CodexNativeSessionLauncher` protocol through a deterministic
  executable at the external runtime boundary;
- the materialized production stage finalizer for every agent stage;
- production contracts, gates, evidence, sealing, checkpoints, invalidation,
  waits, resumes, reconciliation, and transitions;
- the real deterministic CAD verifier in both Make and Playtest;
- Factory behavior through deterministic doubles only at its outbound remote
  transport boundary;
- write-ownership, durable-proof, topology-coverage, credential-isolation, and
  forbidden-internal-mock checks;
- repair, publication, ambiguous-effect, stale-proposal, and artifact-tamper
  failure paths.

The current Concept-branch implementation must not be merged unchanged. Its
Concept stage and private-Deliver expectations must first be replaced with the
current-main topology. When Concept is later activated, the topology guard
will require that feature change to update the deterministic trace in the same
pull request.

### QA-2: Real-Codex mock-session acceptance

Rewrite and merge the useful work from commits `1853cfd`, `69afa5c`, and
`e4eb604` against current `main`. This tier must prove that one authenticated,
persistent Codex session can:

- start once and resume the exact same session for later stages;
- discover the materialized product-run constitution and skills;
- interpret the current `STAGE.json` and accepted upstream artifacts;
- author minimal stage-appropriate outputs and invoke the normal finalizer;
- bind context proofs to final source bytes and run-root stage inputs;
- pass through production host gates and reach current terminal Release;
- avoid prohibited web, credential, external-effect, and unnecessary subagent
  activity.

This test belongs in `main`, but it is not a required check for every pull
request. Run it manually before high-risk workflow merges and, when desired,
from operator-managed scheduling outside repository automation. Ordinary CI
must remain offline and deterministic.

## Phase 2: Integrate independent fixes

### Runtime Python launcher preservation

Port the intent of `b2e5b9b` into the current runtime policy. Preserve the
newer sandbox and trusted-runtime implementation from `main`; change only the
selection and exact binding of `WORKSHOP_PYTHON` so a managed virtual
environment does not silently fall back to its base interpreter.

### Native process stream cleanup

Reassess `50fff85` against the current process-session guard. Add focused tests
for success, failure, timeout, and forced reaping, then close only the streams
still left open by the current implementation.

### Make finalizer and host parity

Port the failure intent of `db83d57` against today's `NativeMade` contract.
For `27d5950`, retain the invariant that a fresh verifier replay cannot
silently mutate sealed CAD source, but do not restore the old blanket
source-clean or `--no-report` policy over the newer reproducible CAD gate.

### Factory nested primary output

Port `1a19157` using current product inventory and primary-model metadata.
Accept exactly one declared, hash-bound assembled output and reject ambiguous
nested candidates. Do not port `d8b48d3`; current `main` already accepts native
Made artifacts without requiring legacy `project.json`.

## Phase 3: Restore Concept incrementally

### Dormant Concept contracts and gate

Restore the Concept schema, contract types, structural gate, package data, and
focused tests without changing the production lifecycle. Include:

- exact routed-Wish identity, objective, and context preservation from
  `948a34d`;
- repair-round freshness from `ea34822`;
- current Inventor-selection, Invent, blueprint, Taste, and artifact hash
  bindings, including Spark's combined selection-and-Make source.

Keeping this layer dormant makes the data boundary independently reviewable
before it can affect a live product run.

### Pre-render Concept proposal protocol

Rebuild the useful parts of `25e647d` and `c2873bd`:

- Codex finalizes a pre-render proposal containing the Concept source
  documents and path-only descriptor;
- the finalizer validates the same structural constraints the host will
  require;
- no rendered image or sealed Concept is required for agent finalization;
- the host alone renders images, binds their hashes, and seals the completed
  Concept.

Do not restore the feature branch's quiet-period completion fallback. Current
`main` has a newer fail-closed finalization watcher and process-session reaper.

### Durable Concept image-effect boundary

Complete `harden-concept-image-effect-boundary` before enabling paid Concept
rendering. The host must own:

- explicit private-data transmission authorization;
- a durable intent written before transmission;
- a stable idempotency identity;
- provider operation identity and authenticated reconciliation;
- verified receipts bound to exact returned bytes;
- an explicit unknown-outcome state that prevents blind retry;
- a gate that consumes receipts and exact bytes without making a remote call.

Provider request/response compatibility from `e189bcb` belongs at this
boundary. Its obsolete CAD timestamp and `--no-report` workarounds do not.

### Activate Concept in the current lifecycle

Only after the contracts, pre-render protocol, image-effect boundary, and both
QA tiers are ready, define Concept's position in each selectable effort route
in a new architecture decision. The historical feature-branch sketch was:

```text
Wish -> Match -> Invent -> Concept -> Make <-> Playtest -> terminal Release
```

Do not activate that fixed topology unchanged: new runs have no Match turn,
Spark and Forge pass Playtest through, and passed-through stages may not create
a turn, artifact, gate, or evidence. Any Concept activation must preserve
those effort semantics or explicitly supersede ADR 0016.

Route Playtest feedback by invalidation scope:

```text
build-only feedback       -> Make
design-level feedback     -> Concept
invention-level feedback  -> Invent
```

This activation change must update the authoritative topology, deterministic
E2E trace, real-Codex mock-session trace, product-run instructions, lifecycle
documentation, checkpoint invalidation, and wait/resume scenarios together.

## Source commit disposition

| Commit | Subject | Disposition |
|---|---|---|
| `25e647d` | Fix Concept finalization before image rendering | Reimplement in pre-render Concept protocol |
| `c2873bd` | Fix native completion and Concept brief validation | Keep validation; drop obsolete completion fallback |
| `ea34822` | Reject stale Concept contracts across repair rounds | Port with Concept contracts |
| `febb478` | Backlog Concept image-effect hardening | Preserve and complete before activation |
| `1853cfd` | Add real-Codex mock-session acceptance | Rewritten and merged as effort-aware published-Release acceptance |
| `b2e5b9b` | Preserve the Workshop Python environment | Port early against current sandbox policy |
| `50fff85` | Close native Codex process streams | Reassess and port as focused cleanup |
| `948a34d` | Enforce exact routed Wish context | Port with Concept contracts |
| `db83d57` | Validate Make product metadata before handoff | Adapt to current `NativeMade` contract |
| `27d5950` | Require source-clean replayable CAD | Preserve invariant; do not transplant old policy |
| `d8b48d3` | Accept canonical Make metadata handoff | Superseded by `main` |
| `1a19157` | Select sealed nested assembled output | Adapt to current Factory inventory |
| `69afa5c` | Bind E2E context proof to final source bytes | Rewritten and merged into the effort-aware mock-session tier |
| `e4eb604` | Audit only run-root stage bindings | Rewritten and merged into the effort-aware mock-session tier |
| `9a979e0` | Complete old mock-session OpenSpec tasks | Reconciled and superseded by the current-route rewrite |
| `e189bcb` | Harden Concept rendering and native CAD verification | Split provider/Concept work from obsolete CAD workarounds |

## Per-change merge discipline

For every pull request in this train:

1. Create a fresh branch from the latest `origin/main`.
2. Port or write the focused failure scenario first.
3. Confirm that it fails for the intended reason.
4. Implement the smallest current-architecture change that makes it pass.
5. Run component and integration tests for every affected boundary.
6. Run deterministic E2E for lifecycle, gate, artifact, or effect changes.
7. Run the real-Codex acceptance tier before high-risk workflow merges.
8. Rebase once immediately before merge and resolve against current behavior,
   not the historical feature implementation.
9. Merge before beginning the next dependent slice.
10. Update the commit-disposition ledger to `merged`, `superseded`,
    `rewritten`, or `deferred`.

## Completion criteria

The Concept branch is fully reconciled when:

- every source commit has a final disposition;
- both QA layers are present on `main` with accurately scoped evidence claims;
- all retained independent fixes are integrated or explicitly superseded;
- Concept is active only with its durable image-effect boundary;
- deterministic and real-Codex traces cover the same authoritative lifecycle;
- current documentation describes implemented behavior rather than the old
  feature branch; and
- `feat/concept-phase` is no longer needed as an implementation branch.
