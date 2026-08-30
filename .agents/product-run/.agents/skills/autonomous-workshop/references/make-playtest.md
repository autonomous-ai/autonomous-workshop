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
the current checkpoint, or—only for a build-blocking contradiction in a sealed
Forge/Quest Invent contract—a successful `make-revision` finalizer.

For Forge and Quest, the sealed Invent result is the primary reference for
form, proportion, construction, component breakdown, and intended interaction.
Read both its selected `concept` and `research`; preserve its explicit
dimensions and constraints. For Spark, `STAGE.json` sets
`creative_source_required: true`: compare the complete roster, select the
best-fit Inventor, use that custom agent, and write one compact authored source
with exactly `selected_inventor_id`, roster-covering `ranking`, `concept`, and
`research`. The Make finalizer seals those bindings together with the Made
contract, so Spark still has exact creative provenance without another turn.

For Spark, scan the roster's bounded agent descriptions in one pass, rank the
complete roster, and open the full Taste and skill bundle only for the selected
Inventor. Define one signature interaction and one anti-generic visual or
mechanical signature before CAD. A compact toy with one extraordinary moment
is stronger than a feature list whose parts receive shallow treatment.

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

Keep Make finishable within the native turn boundary. The root Manager owns the
critical path and must establish an actual conforming CAD baseline plus its
deterministic verifier early. Delegate only concrete bounded mechanism, CAD, or
review tasks; never delegate the whole build or wait indefinitely for a child
before progressing. Once required checks and direct inspection pass, prioritize
the finalizer over optional additional exploration. A recovery turn after a
host timeout must inspect and reuse existing product bytes rather than restart
the design or repeat completed subagent work.

Use one deliberate verification funnel. During source edits, build the smallest
entry that exposes the changed relationship and run only its relevant narrow
check. After the geometry and signature interaction stabilize, batch exports,
run the integrated final verifier once, create the presentation render, inspect
it, fix the largest visible defect, and finalize. Do not repeatedly run a full
fresh verifier or regenerate unchanged exports between small edits.

If a concrete operator or environment condition makes safe Make progress
impossible, use the main skill's `need` finalizer for the current `make` stage
and return control without claiming Goal completion. Use `waiting` for a
resolvable condition and `failed` only when safe continuation is impossible.
Do not use that path for ordinary CAD difficulty, a repairable verifier or
finalizer error, or a sealed Invent contradiction eligible for the
evidence-bound `make-revision` route below.

## Return an unbuildable sealed concept to Invent

For Forge and Quest, `STAGE.json` may set `invent_revision_allowed: true` and
provide canonical revision contract and evidence paths. Use that path only
when exact inspection proves that the sealed Invent concept is internally
contradictory, omits a decision required for every conforming implementation,
or otherwise makes truthful Make completion impossible. A difficult build,
ordinary CAD mistake, aesthetic preference, or repair that can preserve the
concept stays inside the current Make Goal.

Do not edit sealed Invent bytes or silently depart from them. Preserve exact
deterministic or independently inspected findings under
`invent_revision_evidence_root`. Write one source JSON with exactly `feedback`.
Every feedback item must use severity `block`, cite at least one file from that
evidence tree, state the contradiction and required design change, and use:

```json
{"invalidates":["invent","make","playtest","release"]}
```

Then run:

```bash
"$WORKSHOP_PYTHON" .agents/skills/autonomous-workshop/scripts/stage_proposal.py \
  --run-root . make-revision \
  --source <make-revision-source.json> \
  --evidence-root <STAGE invent_revision_evidence_root>
```

The finalizer succeeds by sealing a truthful failed-Make proposal, not a Made
artifact. Return control immediately. The host rehashes the evidence, verifies
its exact assignment/Invented bindings and shared round budget, then alone may
invalidate Invent and downstream stages and start a new Invent Goal. The
revised Invent packet receives the prior concept and exact Make feedback.

Leave the product tree at the exact `product_root` in `STAGE.json`. It must
include the required root product metadata, CAD project, assembled STEP/STL
outputs, and deterministic CAD verification file. Map mechanisms, rules,
dimensions, materials, tolerances, and limitations to real artifact bytes
rather than prose assertions.

Keep stable exported STEP/STL/GLB files, product PNG renders, source, and
measurements in the product tree. Do not preserve `__cadgen__` runtime caches,
generation locks/progress files, `__pycache__`, or temporary work trees there:
the host's `--fresh` verifier intentionally rebuilds those bytes. The Make
finalizer removes safe regular cache files before hashing and fails closed on
linked, special, or unremovable cache content. If the sandbox protects a now
empty cache directory from unlink, leave it in place: byte-free directories
are ignored by both the finalizer and the host's exact-file gate. Frozen older
finalizers may rely on the trusted host to prune that empty residue before a
later resume; do not treat the directory itself as product evidence.

Create and inspect an actual presentation render at
`<cad-project>/snap/iso.png` before finalizing. Use the CAD skill's
`scripts/render_product` on an exact verified STL, or another deterministic
renderer that writes the same path. The image must be a valid chromatic
RGB/RGBA PNG at least 800 px on each side. Choose a palette and view that make
the product's form and play affordance legible. Binary silhouettes from
`image-to-cad/render_views.py` are measurement evidence, not product renders;
keep them in a clearly named review/evidence directory. The finalizer rejects
a missing, grayscale, flat, or undersized presentation image, and the public
snapshot promotes only this explicit `snap/` render family as its local hero.

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

For every required check id `<check-id>`, write its canonical configuration to
the exact path `<evidence_root>/configs/<check-id>.json`. Each canonical config
is a strict JSON object with `schema_version: 1`, the exact `check_id`, and the
current Made product-manifest hash under
`product_artifact_sha256` (preferred) or the legacy `artifact_sha256` key. If
both binding keys are present, they must agree. A config may preserve any
additional finite JSON needed to reproduce or audit that check; when `seed` is
present it must be an integer. The finalizer seals every config byte, and the
host independently rehashes it and verifies the current Made binding.

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

If `STAGE.json` contains `host_playtest_proposal_rejection`, read its exact
failure code and feedback before repairing the evidence. The host quarantined
the rejected proposal because its config, evidence, or contract could not be
safely reopened or rebound. Replace linked, missing, special, or changed files
with stable regular files and regenerate the proposal; never weaken the check.

Choose each actionable feedback boundary explicitly:

- implementation repair: `["playtest", "release"]`, returning to Make;
- concept revision: `["invent", "make", "playtest", "release"]`,
  returning to Invent with the exact prior design and evidence.

Route concept-invalidating Playtest evidence directly to Invent. Do not spend
an intermediate Make Goal merely forwarding evidence that Make cannot resolve.

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
