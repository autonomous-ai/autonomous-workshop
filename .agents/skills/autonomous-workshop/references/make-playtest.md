# Make and Playtest contracts

Read `STAGE.json`. It binds the exact sealed upstream artifacts, lane blueprint,
canonical output paths, current round, round limit, and any prior Playtest
feedback. Verify those bytes before acting.

## Make

**Input:** Sealed Invent output, exact upstream bindings, prior Playtest
feedback, lane requirements, and deterministic tool policy.

**Codex work:** Use native editing and the materialized `cad`,
`product-to-cad`, and `step-parts` skills under `.agents/skills/` to create the
actual product project. Inspect renders and files, run their narrow
deterministic checkers, and repair concrete findings within the round budget.
Map mechanisms, rules, dimensions, materials, tolerances, and limitations to
real artifact bytes rather than prose assertions.

**Artifact and gate:** Leave the product tree at the exact `product_root` from
`STAGE.json`. It must include the required root product metadata, CAD project,
assembled STEP/STL outputs, and a deterministic CAD verification file. Then
run:

```bash
python .agents/skills/autonomous-workshop/scripts/stage_proposal.py \
  --run-root . make \
  --product-root <STAGE product_root> \
  --cad-project-path <path inside product root> \
  --cad-verification-path <path inside product root>
```

The finalizer hashes the complete tree and writes the canonical Made contract.
The host independently copies the tree into an isolated verifier, reruns the
trusted CAD gate, compares exact bytes, and seals the accepted tree. A passing
narrative never overrides a failed or absent measurement.

## Playtest

**Input:** One sealed Make revision, its exact manifest/hash, lane tasks, and
the required check ids in `STAGE.json`.

**Codex work:** Review the exact artifact from first-time, optimizing,
exploratory, and adversarial player perspectives. Run the required seeded
simulations and artifact inspections through narrow tools. Keep model judgment
separate from deterministic observations; never invent physical or human test
results.

**Artifact and gate:** Leave the exact evidence tree requested by `STAGE.json`
and one authored JSON source with exactly `checks`, `feedback`, and `verdict`.
Every required check id must appear once and cite its config and evidence file.
Then run:

```bash
python .agents/skills/autonomous-workshop/scripts/stage_proposal.py \
  --run-root . playtest \
  --source <playtest-source.json> \
  --evidence-root <STAGE evidence_root>
```

The host validates the canonical Playtested contract, exact evidence tree, and
reruns the trusted CAD gate. Any `improve` or `block` verdict must have
actionable, evidence-linked feedback and returns to Make. It consumes a bounded
round and invalidates downstream evidence. Only a pass for the current Made
artifact advances to Release.
