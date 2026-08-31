## Why

The current workflow has the two acceptance layers required by the adopted Concept integration plan, but `main` no longer contains the deterministic Concept contract and gate code needed for a safe incremental restoration. Reintroducing that boundary as dormant, route-aware infrastructure now creates a reviewable foundation for folding Concept work into the first active creative stage without reviving the source branch's obsolete Match turn, standalone Concept stage, fixed lifecycle, inline image effect, or private Deliver ending.

## What Changes

- Restore versioned Concept source, pre-render, and sealed-contract types, exact-byte manifests, JSON schema/package data, and deterministic structural validation adapted from `feat/concept-phase`.
- Bind every Concept contract to the exact routed Wish, assignment, selected Taste, universal blueprint, Invented contract, creative-source bytes, round, and revision inputs; support both Forge/Quest Invent provenance and Spark's folded selection-and-Make provenance without selecting an active route.
- Reject stale repair-round contracts, routed-Wish rewrites, unsafe paths, duplicate or malformed JSON, inconsistent descriptors, incomplete briefs/research/instructions, and changed artifact bytes.
- Reconcile the existing Concept-related specs with current behavior: these contracts are dormant and MUST NOT add a stage, turn, Goal, packet, transition, gate decision, Make binding, Playtest edge, wait state, credential, network call, or external effect.
- Fix the future integration direction: Concept SHALL NOT return as a standalone lifecycle stage. A later activation change will fold Concept authoring and sealing into the first active creative stage—Invent for Forge/Quest and folded Make for Spark—while keeping the native creative turn separate from host-owned image effects.
- Preserve the current Spark, Forge, and Quest routes and terminal published Release behavior unchanged.
- Record source-branch disposition for the contract-only portions of `948a34d` and `ea34822`; leave compound creative-stage finalizer wiring, durable image effects, and merged-boundary activation for later changes in the integration plan.

## Capabilities

### New Capabilities

- `workshop/concept-contracts`: Defines dormant, content-addressed Concept contracts and deterministic structural validation with exact route provenance and repair freshness.

### Modified Capabilities

- `workshop/concept-stage`: Replaces the stale active-stage requirement with an explicit dormant sub-boundary that can later be folded into Invent or Spark Make but can never create a standalone Concept stage.
- `workshop/concept-images`: Separates authored pre-render source and path-only descriptors from host-sealed image bytes while keeping both forms dormant.
- `workshop/concept-image-integration`: Defers provider execution and forbids this change from making network or credential-bearing image calls.
- `workshop/make-concept-adherence`: Keeps current Make inputs and gates unchanged; Concept adherence remains inactive until the merged creative boundary is activated.
- `workshop/wish-research`: Retains exact routed-Wish preservation and research attribution as deterministic contract rules without activating a separate Concept research turn.

## Impact

- Adds a dormant `src/workshop/concept/` contract/gate package, its owned schema, package-data registration, and focused unit/packaging tests.
- Updates Concept integration documentation and the source-commit disposition ledger to distinguish restored contract behavior from deferred protocol/effect/lifecycle work.
- Does not alter `src/workshop/workflow/`, runtime stage sequencing, `.agents/product-run/`, the run-local finalizer, Make/Playtest/Release contracts, Factory publication, credentials, or remote transports.
- No current run topology or public CLI behavior changes; historical and effort-aware checkpoints keep their existing frozen protocols.
