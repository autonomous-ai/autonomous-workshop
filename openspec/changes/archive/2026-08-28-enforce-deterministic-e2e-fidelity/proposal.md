## Why

The current deterministic full-run test can show that a route reached Release
while still treating an enabled phase as one abstract fixture operation. That
misses regressions inside Invent, Make, Playtest, and Release—the exact
finalizer, contracts, artifact ownership, deterministic checks, evidence, and
checkpoint mutations that make the run trustworthy.

## What Changes

- Define deterministic E2E fidelity phase by phase. Wish must prove exact input
  persistence and its host gate; Invent must prove roster-bound selection,
  research/concept source finalization, both sealed contracts, and its gate;
  Make must prove agent-owned product/CAD authorship, materialized
  finalization, fresh production CAD verification, manifest sealing, and its
  checkpoint; Playtest must prove exact Made replay, deterministic evidence,
  verdict/feedback handling, invalidation, and repair; Release must prove
  package authorship, PDF and claim validation, CAD replay, Factory effect
  intent, reconciliation, publication, public hash readback, receipt, and the
  terminal checkpoint.
- Exercise those internals through the real lifecycle for Spark
  (`Wish -> Make -> Release`), Forge (`Wish -> Invent -> Make -> Release`), and
  Quest (`Wish -> Invent -> Make <-> Playtest -> Release`). Folded selection is
  proven inside Spark Make or Forge/Quest Invent; passed-through phases must
  leave no turn, contract, gate, evidence, or placeholder success.
- Replace live cognition only with a deterministic executable at the native
  process boundary. It speaks the supported version/start/resume/JSONL
  protocol, authors fixed agent-owned source bytes, and invokes the exact
  materialized `stage_proposal.py`; production code still owns all accepted
  contracts, gates, sealing, checkpoints, and transitions.
- Replace Factory only at outbound transports. Keep production credential
  loading, request validation, effect persistence, idempotency,
  reconciliation, promotion, authenticated/public readback, and receipt
  validation active.
- Add phase-proof and artifact-ownership guards that fail if a phase merely
  reports success, if a required durable output disappears, or if a double
  creates host-owned output. Add a policy guard against internal patching and a
  topology guard that requires phase-level proof for every enabled route and
  transition.
- Cover input-driven stale proposal, post-finalizer tamper, CAD rejection,
  Quest repair, missing-credential wait/resume, ambiguous publication,
  irreconcilable/tampered effect state, and clean-run repeatability cases at
  the production boundary where each failure belongs.
- Run the offline suite as a separate required CI job and document its runtime
  and evidence limits. It does not evaluate model quality or prove physical
  manufacture, fit, durability, delivery, or human response.

## Capabilities

### New Capabilities

- `workshop/deterministic-e2e-fidelity`: Defines an offline, repeatable test
  boundary for the production native lifecycle, phase-specific durable proof,
  and deterministic doubles restricted to process-external dependencies.

### Modified Capabilities

None.

## Impact

- Adds a deterministic native executable, phase-proof helpers, external
  Factory protocol service, policy/topology guards, and route/failure scenarios
  under `tests/end_to_end/`.
- May add only the narrow outbound Factory transport seam needed to drive the
  production integration offline; no workflow-level test mode or phase
  replacement is introduced.
- Exercises the materialized finalizer and production CAD/PDF/Factory paths,
  so it runs as a required, separately named CI job rather than a fast unit
  test.
- Does not activate Concept or Match as standalone stages, restore private
  Deliver, call a live model or service, or claim evidence of physical manufacture, fit, durability,
  delivery, or human response.
