# Make and Playtest contracts

The host supplies the native session identity, absolute workspace, durable
checkpoint, exact sealed upstream artifacts, capability limits, current round,
round budget, and authorization scope. Verify them before acting.

## Make

**Input:** Sealed Invent output, exact upstream bindings, prior Playtest
feedback, lane requirements, and deterministic tool policy.

**Codex work:** Use native editing and the materialized `cad`,
`product-to-cad`, and `step-parts` skills under `.agents/skills/` to create the
actual product project. Inspect renders and files, run their narrow
deterministic checkers, and repair concrete findings within the round budget.
Map mechanisms, rules, dimensions, materials, tolerances, and limitations to
real artifact bytes rather than prose assertions.

**Artifact and gate:** Leave a complete artifact tree, content-addressed
manifest, product summary, and required CAD/manufacturing verification
receipts. Return only compact paths, hashes, gate evidence, needs, and a
proposed transition. The host seals the exact bytes and validates the canonical
`Made` and CAD release contracts. A passing narrative never overrides a failed
or absent measurement.

## Playtest

**Input:** One sealed Make revision, its exact manifest/hash, lane tasks,
deterministic evidence, and fixed goal.

**Codex work:** Review the exact artifact from first-time, optimizing,
exploratory, and adversarial player perspectives. Run the required seeded
simulations and artifact inspections through narrow tools. Keep model judgment
separate from deterministic observations; never invent physical or human test
results.

**Artifact and gate:** Leave artifact-bound Playtest evidence plus structured,
evidence-linked feedback. The host validates the canonical `Playtested`
contract. Any `improve` or `block` finding returns to Make, consumes a bounded
round, and invalidates Playtest, Instructions, and Deliver evidence for the old
bytes. Only a pass for the current artifact advances.
