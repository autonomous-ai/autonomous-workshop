# ADR 0018: Evidence-bound Make-to-Invent revision

- Status: Accepted
- Date: 2026-08-27
- Owners: Make, Invent, Workflow, Runtime
- Relates to: ADR 0012 (native session), ADR 0016 (effort routes)

## Context

A production Quest run reached Make with a sealed concept whose physical
requirements contradicted one another. The native Manager preserved a
deterministic contradiction check and a written diagnosis, but Make had no
authorized finalizer or host transition that could return this evidence to
Invent. Repeating Make could not repair a concept-level impossibility, while
pretending to produce a Made artifact would have weakened the gate.

Quest already allowed Playtest to return directly to Make for implementation
defects or directly to Invent for concept defects. That did not help when the
contradiction became provable before any conforming Made artifact existed.

## Decision

New Forge and Quest workspaces freeze a versioned Make-to-Invent capability.
When, and only when, the sealed Invent contract prevents a conforming build,
the active Make Goal may finalize a block-level revision request. It must bind:

- the current round and exact Wish, assignment, and Invented hashes;
- the exact authored request source;
- a canonical evidence directory and rehashable artifact manifest;
- block-level feedback with the exact invalidation boundary
  `invent, make, playtest, release`; and
- the final revision-request hash.

The host independently validates and seals those bytes, records a failed Make
gate, consumes the shared lifecycle revision budget, invalidates Invent and all
downstream stages, and starts a new Invent Goal with the exact request. The
host does not judge the prose or invent a repair.

Playtest retains its direct routes. It returns to Make for an implementation
defect and to Invent for a concept defect; it does not route a known concept
defect through a redundant Make Goal. Spark keeps concept selection inside Make
and therefore has no Make-to-Invent edge.

## Alternatives considered

### Keep retrying Make

Rejected. A new Make attempt cannot make contradictory sealed requirements
conform, and repeated attempts waste bounded native turns without changing the
authoritative concept.

### Route every Playtest failure through Make

Rejected. It blurs ownership and adds a Goal whose only useful act would be to
forward evidence already available to Invent.

### Let the host infer whether a concept is impossible

Rejected. Semantic diagnosis belongs to the native agent. The trusted host
validates exact contracts, hashes, evidence, budgets, and transitions only.

## Consequences

Every active stage attempt still has one native Goal, and only one Goal is
active at a time. The new edge is auditable and bounded rather than an open
agent loop. Normal CAD, fit, or fabrication defects remain inside Make. Public
toy snapshots can preserve the failed gate, request, authored source, and its
safe evidence beside later successful revisions.

## Compatibility and migration

Capability is frozen by a versioned reference file in the materialized
product-run protocol. Older runs without that exact marker continue under their
original topology. Spark rejects the request. Resume never upgrades a frozen
run implicitly.

## Verification

Contract tests cover exact context binding, evidence rehashing, tampering,
severity, and absent evidence. Workflow and gate tests cover effort and frozen
capability restrictions, invalidation, and budget exhaustion. The deterministic
native full-run test executes:

```text
Wish -> Invent -> Make (blocked) -> Invent -> Make -> Playtest -> Release
```

Production acceptance additionally requires a real CLI Wish, one persistent
native session, authenticated Factory publication/readback, and a sanitized Git
snapshot of the real Inventor and toy.
