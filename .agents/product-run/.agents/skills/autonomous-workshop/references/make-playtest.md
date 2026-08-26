# Make and Playtest contracts

Read `STAGE.json`. It binds the exact sealed upstream artifacts, universal
blueprint, canonical output paths, current round, round limit, and any prior
Playtest feedback. Verify those bytes before acting. Host rounds and
checkpoints bound the work; Codex performs the reasoning and repair.

## Make Goal and improvement loop

Create one native Codex Goal for the current Make attempt. Its objective is to
produce the exact buildable, inspectable product artifact required by the
sealed Invent output and, on a later round, repair the failures cited by the
prior Playtest. Its stopping condition is a successful `make` finalizer for
the current checkpoint.

While pursuing the Goal:

1. **Observe:** Inspect the Invent concept, selected Inventor instructions,
   universal blueprint, current revision workspace, deterministic tool policy,
   and every evidence-linked feedback item from a prior Playtest.
2. **Act:** Use native editing and the materialized `cad`, `product-to-cad`,
   and `step-parts` skills under `.agents/skills/` to create or repair the
   actual product artifact. Use native subagents for bounded mechanism, CAD, or
   review tasks when useful.
3. **Evaluate:** Build the artifact, run narrow deterministic checkers, inspect
   actual STEP/STL and rendered outputs, and compare observed behavior with the
   concept, dimensions, materials, tolerances, assembly, and prior feedback.
   Use an independent native reviewer for subjective or adversarial inspection
   where it adds evidence.
4. **Improve:** Fix the largest concrete failure, rebuild, rerun the checks,
   and reinspect the artifact. Keep changes focused enough to know whether the
   evidence improved. Continue within the host-provided round.

Codex owns the build/check/inspect/repair loop. Python tools may generate CAD,
measure exact geometry, or validate a contract; they do not plan repairs,
score Taste, route agents, or control the loop.

Leave the product tree at the exact `product_root` in `STAGE.json`. It must
include the required root product metadata, CAD project, assembled STEP/STL
outputs, and deterministic CAD verification file. Map mechanisms, rules,
dimensions, materials, tolerances, and limitations to real artifact bytes
rather than prose assertions. Then run:

```bash
python .agents/skills/autonomous-workshop/scripts/stage_proposal.py \
  --run-root . make \
  --product-root <STAGE product_root> \
  --cad-project-path <path inside product root> \
  --cad-verification-path <path inside product root>
```

The deterministic finalizer hashes the complete tree and writes the canonical
Made contract. Complete the Make Goal only after it succeeds, then return to
the host. The host copies the exact tree into an isolated verifier, reruns the
trusted CAD gate, compares bytes, and seals the accepted revision. Narrative
or model confidence never overrides a failed or absent measurement.

## Playtest Goal and independent evidence loop

Create one native Codex Goal for the current Playtest attempt. Its objective is
to independently evaluate the one sealed Made revision and produce complete,
reproducible evidence with a truthful `pass`, `improve`, or `block` verdict.
Its stopping condition is a successful `playtest` finalizer for the current
checkpoint. Finalizing an evidence-backed failure satisfies the Playtest Goal;
passing the product is not required when the evidence says it fails.

The universal baseline requires exactly these check ids unless the current
`STAGE.json` states otherwise:

- `agent-playtest`
- `mechanical-check`
- `printability-check`

Product-specific risks may justify additional inspections and evidence, but
never omit or rename the host-required checks.

All three baseline results are Codex-authored digital assessments unless the
host supplies replayed deterministic evidence or an authenticated physical
receipt that explicitly proves more. A digital mechanical or printability
assessment never proves successful printing, physical fit, durability, or
human play.

While pursuing the Goal:

1. **Observe:** Inspect the exact sealed Made tree, its manifest, required
   check ids, test configurations, rendered outputs, and the product's stated
   rules and claims. Establish a baseline before judging it.
2. **Act:** Use independent native subagents for first-time, optimizing,
   exploratory, and adversarial player perspectives. Run required seeded
   simulations and artifact inspections through the narrow deterministic
   tools. Preserve each configuration and output as exact evidence.
3. **Evaluate:** Compare each observation with its rubric and artifact bytes.
   Keep native-agent judgment separate from deterministic measurements. Check
   evidence coverage, reproducibility, and whether feedback names a concrete
   failure and repair direction.
4. **Improve:** Repair missing or weak test evidence, rerun invalid tests, and
   sharpen feedback. Do not modify the sealed Made product during Playtest or
   reason a failed check into a pass.

Leave the exact evidence tree requested by `STAGE.json` and one authored JSON
source with exactly `checks`, `feedback`, and `verdict`. Every required check
id must appear once and cite its config and evidence file. Never invent
physical trials, human players, measurements, or results. Then run:

```bash
python .agents/skills/autonomous-workshop/scripts/stage_proposal.py \
  --run-root . playtest \
  --source <playtest-source.json> \
  --evidence-root <STAGE evidence_root>
```

The deterministic finalizer validates evidence coverage and writes the
canonical Playtested contract. Complete the Playtest Goal after it succeeds
and return to the host, regardless of the truthful verdict.

For `improve` or `block`, the host alone consumes a bounded round, invalidates
downstream evidence, and checkpoints the transition back to Make. The host
does not interpret or repair the product. In the next Make Goal, Codex reads
the exact feedback, decides the repair, and runs the new build/evaluation loop.
Only a host-verified pass for the current Made bytes can advance to Release.
