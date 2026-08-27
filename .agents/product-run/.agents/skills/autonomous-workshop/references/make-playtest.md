# Make and Playtest contracts

Read `STAGE.json`. It binds the exact sealed upstream artifacts, universal
blueprint, canonical output paths, current round, round limit, and any prior
Playtest feedback. Verify those bytes before acting. Host rounds and
checkpoints bound the work; Codex performs the reasoning and repair.

`inputs.vault_leads` lists what the design vault records against the sealed
concept's mechanisms: `risk` entries with the anti-pattern, the recorded
`suggested_fixes`, banked `evidence`, and a stable `id`. They are computed
from the run's immutable vault snapshot, not authored by a model. Read them
before building and before judging; a lead is a lead, not a verdict.

`inputs.prior_evidence` lists what earlier runs sharing these mechanisms
already broke on: each row is one sealed Playtest finding with its severity,
the fix that was tried, its provenance weight (a measurement outranks a model
assessment), and the vault symptom it confirmed, if any. This run's own rows
are never included and the block is capped at ten. Treat rows as leads with
history, not as verdicts about this revision.

## Make Goal and improvement loop

Create one native Codex Goal for the current Make attempt. Its objective is to
produce the exact buildable, inspectable product artifact required by the
sealed Invent output and, on a later round, repair the failures cited by the
prior Playtest. Its stopping condition is a successful `make` finalizer for
the current checkpoint.

The sealed Invent result is the primary reference for form, proportion,
construction, component breakdown, and intended interaction. Read both its
selected `concept` and its `research`; preserve its explicit dimensions and
constraints, and do not reinterpret the Wish from scratch. Realize every
component and interface the selected concept names in the actual product tree.

While pursuing the Goal:

1. **Observe:** Inspect the sealed Invent concept and research, the selected
   Inventor instructions, universal blueprint, current revision workspace,
   deterministic tool policy, and every evidence-linked feedback item from a
   prior Playtest. `STAGE.json` also carries `score_history` (every prior
   round's medians and spreads), `regression` (dimensions the last repair
   made worse, with the delta), and `ambiguous` (dimensions readers disagreed
   on). A repair that fixes the cited failure while a regression grows is not
   an improvement; address the regression in the same round. When the host
   sets `repair_base`, the previous round scored strictly worse than an
   earlier sealed round by machine counts (failing checks plus actionable
   feedback): start this round's repair from that sealed `product_root` and
   `made_sha256`, not from the last revision.
2. **Act:** Use native editing and the materialized `cad`, `image-to-cad`,
   `design-reference`, and `step-parts` skills under `.agents/skills/` to
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

### Build one group at a time

The sealed concept's `build_plan` orders its components into groups. Inside
the Make Goal, work group by group rather than building the whole tree in one
pass: build only that group's parts, export each one to
`<product_root>/parts/<component key>.stl` in print orientation, run the
deterministic checks, inspect the result, then seal the group:

```bash
"$WORKSHOP_PYTHON" .agents/skills/autonomous-workshop/scripts/stage_proposal.py \
  --run-root . make-group --product-root <STAGE product_root> --group <group>
```

The finalizer records the exact part bytes under `groups/<group>.json`. If a
group cannot be sealed after focused repair, stop the Goal with a truthful
need instead of building later groups on it — later groups mate with this
one. The `make` finalizer refuses a tree whose groups are unsealed or whose
parts changed after their group was sealed; re-run `make-group` for that
group after any change to its parts. Concepts sealed before build plans
existed (Invented schema 3 or 4) need no groups.

Leave the product tree at the exact `product_root` in `STAGE.json`. It must
include the required root product metadata, CAD project, assembled STEP/STL
outputs, and deterministic CAD verification file. Map mechanisms, rules,
dimensions, materials, tolerances, and limitations to real artifact bytes
rather than prose assertions. Then run:

```bash
"$WORKSHOP_PYTHON" .agents/skills/autonomous-workshop/scripts/stage_proposal.py \
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

When the deliverable is intentionally digital/mesh-only and is not eligible
for a print-ready claim, declare that limitation in both sealed inputs: set
root `product.json.status` to exactly
`digitally-verified-not-print-ready` and set the declared CAD verification
JSON's `final_pipeline.print_ready_claim` to the literal boolean `false`.
Only that agreeing pair authorizes the host's lower tier, which skips wall
thickness while retaining fresh generation, fit, local spec, mount, motion,
kernel, interference, export, and mesh gates. Never use the status alone,
spell `false` as a string, or describe a lower-tier result as print-ready in
Playtest evidence, Release facts, the manual, or product copy. Omit the lower
tier declarations for a print-ready-eligible artifact; the host then requires
the wall-thickness gate.

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

Keep replay work separate from evidence and treat the sealed Made tree as
strictly read-only. Run temporary wrappers, copied inputs, caches, and transient
renders under `work/playtest/rNNNN/`, where `NNNN` is the current zero-padded
round. Default to copying only the exact inputs needed into that work area
before executing or importing them. A tool may read sealed bytes in place only
when it is known not to write beside its input. For Python or CAD tooling, set
`PYTHONDONTWRITEBYTECODE=1` and redirect `XDG_CACHE_HOME`, `TMPDIR`, `TMP`, and
`TEMP` into the work area; never leave `__pycache__`, `__cadgen__`, lock,
progress, or scene-cache files in the Made tree. Record the sealed Made path and
hash, copied-input hash, exact command, seed, and tool version in a canonical
config file. Put only those configs and the final static outputs cited by
checks under the exact `evidence_root`; do not duplicate Made source, working
trees, cache directories, transcripts, or JSONL streams there. Keep the
three-field authored proposal under `drafts/`.

Leave the exact evidence tree requested by `STAGE.json` and one authored JSON
source with exactly `checks`, `feedback`, and `verdict`. Every required check
id must appear once and cite its config and evidence file.

When `STAGE.json` carries `vault_leads`, the `agent-playtest` check's
`observations` must answer every lead once under `vault_leads`:

```json
{"lead": "<id from STAGE.json>", "verdict": "confirmed", "why": "...",
 "feedback_code": "<code of the feedback item that repairs it>"}
{"lead": "<id>", "verdict": "dismissed", "why": "...", "feedback_code": null}
```

A confirmed lead is a risk you observed in this exact revision, so it must
name the feedback item that carries the repair direction; a dismissed lead
says in one sentence why the recorded risk does not apply here. Unanswered,
duplicated, or never-issued lead ids fail the finalizer and the host gate.

When `STAGE.json` carries `score_dimensions`, the same `agent-playtest`
observations must also carry `reads`: at least `score_minimum_reads`
independent native readers, each blind to the others, scoring the sealed
revision 0 to 10 on exactly those dimensions and naming the single concrete
`one_change` that would raise its weakest score most:

```json
{"reader": "first-time-owner", "scores": {"wish_fit": 8, "play": 7,
 "legibility": 6, "build_confidence": 7}, "one_change": "..."}
```

The host keeps the median and the spread per dimension in the gate receipt.
A `pass` verdict is refused when any median sits below `score_floor`. A
spread of 3 or more is a finding about the artifact — readers cannot tell
whether it has that property — not noise to average away. Never invent
physical trials, human players, measurements, or results. Every failing check
must name the concrete product or design area and the repair direction.
Invalidate Playtest and its downstream evidence; the host returns every
evidence-backed failure directly to Make, where the next Goal repairs the
product against the same sealed Invent result. Each feedback `invalidates`
array may therefore contain only `playtest`, `release`, and `deliver`. Do not
put `make` in that array: the failed verdict and proposed transition already
route the work to a new Make attempt. Then run:

```bash
"$WORKSHOP_PYTHON" .agents/skills/autonomous-workshop/scripts/stage_proposal.py \
  --run-root . playtest \
  --source <playtest-source.json> \
  --evidence-root <STAGE evidence_root>
```

The deterministic finalizer validates evidence coverage and writes the
canonical Playtested contract. Complete the Playtest Goal after it succeeds
and return to the host, regardless of the truthful verdict.

For `improve` or `block`, the host alone consumes a bounded round, invalidates
downstream evidence, and checkpoints the transition back to Make. The host
does not interpret or repair the product or design. In the next Make Goal,
Codex reads the exact feedback, decides the repair within the sealed Invent
direction, and runs the new build/evaluation loop. Only a host-verified pass
for the current Made bytes can advance to Release.
