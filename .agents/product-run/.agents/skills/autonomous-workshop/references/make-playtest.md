# Make contract

Read `STAGE.json`. It binds the exact sealed upstream artifacts, universal
blueprint, canonical output paths, current round, and any host rejection
feedback. Verify those bytes before acting. Host checkpoints bound the work;
Codex performs the reasoning and repair.

If `STAGE.json` contains `host_make_proposal_rejection` or
`host_cad_gate_rejection`, the previous Make finalizer did not pass the host
gate. Read the complete rejection and its bounded diagnostics, repair the
exact cited defect, rerun the relevant checks, and verify that the rejected
product or evidence bytes changed before invoking the finalizer again. A
completed Goal for the earlier subject is not completion for this new
rejection-bound attempt. Do not merely regenerate and resubmit the same Made
contract.

## Make Goal and improvement loop

Create one native Codex Goal for the current Make attempt. Its objective is to
produce the exact ready-to-print, inspectable product artifact required by the
current effort. Its stopping condition is a successful `make` finalizer for
the current checkpoint.

For Forge and Quest, the sealed Invent result is the primary reference for
form, proportion, construction, component breakdown, and intended interaction.
Read both its selected `concept` and `research`; preserve its explicit
dimensions and constraints. For Spark, `STAGE.json` sets
`creative_source_required: true`: compare the complete roster, select the
best-fit Inventor, use that custom agent, and write one compact authored source
with exactly `selected_inventor_id`, roster-covering `ranking`, `concept`, and
`research`. The Make finalizer seals those bindings together with the Made
contract, so Spark still has exact creative provenance without another turn.

While pursuing the Goal:

1. **Observe:** Inspect the sealed Invent concept and research, the selected
   Inventor instructions, universal blueprint, current revision workspace,
   deterministic tool policy, and every current host rejection.
2. **Act:** Use native editing and the materialized `cad`, `image-to-cad`,
   `design-reference`, `electromechanical-integration`, and `step-parts`
   skills under `.agents/skills/` to
   create or repair the actual product artifact. Use native subagents for bounded mechanism, CAD, or
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
rather than prose assertions.

The root `product.json` must be a JSON object containing at least these exact
metadata keys (additional product-specific fields are allowed):

```json
{
  "title": "Moon Nook",
  "summary": "A tiny lunar observatory built for tabletop play."
}
```

Both `title` and `summary` must be strings with non-whitespace content and no
more than 2,000 characters. Do not substitute aliases such as `name` or
`description`; the Make finalizer and trusted host require the exact keys.

Then run:

```bash
"$WORKSHOP_PYTHON" .agents/skills/autonomous-workshop/scripts/stage_proposal.py \
  --run-root . make \
  --product-root <STAGE product_root> \
  --cad-project-path <path inside product root> \
  --cad-verification-path <path inside product root>
```

For Spark only, also pass `--source <spark-creative-source.json>` using the
four-field source described above. Do not pass `--source` when `STAGE.json`
already contains sealed `assignment` and `invented` inputs.

The deterministic finalizer hashes the complete tree and writes the canonical
Made contract. Complete the Make Goal only after it succeeds, then return to
the host. The host copies the exact tree into an isolated verifier, reruns the
trusted CAD gate, compares bytes, and seals the accepted revision. Narrative
or model confidence never overrides a failed or absent measurement.

Spark and Forge advance directly to Release and therefore require the full
verifier, including wall thickness and print-ready eligibility, at Make. They
must not simulate Playtest; Release records that it was not run. Quest advances
to the host-authored Playtest stage below.

## Playtest Goal and independent evidence loop

This section applies only when `STAGE.json.stage` is `playtest`, which occurs
only for Quest. Create one native Codex Goal whose objective is to independently
evaluate the exact sealed Made revision and produce complete, reproducible
evidence with a truthful `pass`, `improve`, or `block` verdict. Its stopping
condition is a successful `playtest` finalizer. An evidence-backed failure
satisfies the Goal; never reason a failed check into a pass.

The host packet lists every required check id. Each must appear exactly once,
cite a canonical configuration and static evidence file, and stay bound to the
sealed Made artifact. Digital assessment never proves successful printing,
physical fit, durability, or human play.

While pursuing the Goal:

1. **Observe:** Inspect the exact Made tree, manifest, required checks, rules,
   rendered outputs, and claims without modifying sealed bytes.
2. **Act:** Use independent native subagents and narrow deterministic tools for
   player perspectives, seeded simulations, and artifact inspection. Preserve
   exact configurations and outputs.
3. **Evaluate:** Separate native-agent judgment from deterministic measurement;
   verify evidence coverage, reproducibility, and concrete repair direction.
4. **Improve:** Repair weak evidence and rerun invalid tests, but never edit the
   sealed Made product during Playtest.

Keep transient work under `work/playtest/rNNNN/` and only canonical configs and
final cited outputs under the exact `evidence_root`. Write one authored JSON
source with exactly `checks`, `feedback`, and `verdict`. Every failing check
must name a concrete area and repair.

Choose each actionable feedback boundary explicitly:

- implementation repair: `["playtest", "release"]`, returning to Make;
- concept revision: `["invent", "make", "playtest", "release"]`,
  returning to Invent with the exact prior design and evidence.

Then run:

```bash
"$WORKSHOP_PYTHON" .agents/skills/autonomous-workshop/scripts/stage_proposal.py \
  --run-root . playtest \
  --source <playtest-source.json> \
  --evidence-root <STAGE evidence_root>
```

The host follows the structured invalidation marker mechanically, consumes the
shared round budget, and seals the exact evidence. Complete the Playtest Goal
after finalization and return control regardless of the truthful verdict. Only
a host-verified pass for the current Made bytes advances to Release.
