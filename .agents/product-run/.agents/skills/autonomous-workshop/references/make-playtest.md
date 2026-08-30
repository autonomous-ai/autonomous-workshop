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
Inventor. First name the hardest-to-fake magic: the perception, motion, rule,
transformation, or emotional moment whose loss would make the Wish generic.
Select the Inventor whose Taste owns that magic, not merely the specialist whose
usual fabrication method matches one-piece, support-free, or similar
constraints. Shared domain skills solve fabrication after creative ownership
is correct. Define one signature interaction and one anti-generic visual or
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
check. As soon as a plausible exact draft STL exists, render the candidate and
perform the blind signature review below **before** the expensive integrated
final verifier. Resolve at most one largest visual defect coherently, rebuild
and rerender the exact final candidate, then batch exports and run the
integrated final verifier once. A full verifier must not be used as the inner
visual-design loop. Do not repeatedly run it or regenerate unchanged exports
between small edits.

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

The `--cad-project-path` value is the self-contained project the trusted host
will copy into isolation and rebuild. Put its combined generator/import entry,
local helper source, `snap/` family, and final `measure/verification-pipeline.md`
inside that exact directory. Root-level assembled STEP/STL files are delivery
copies, not a substitute for a build entry inside the declared project. Run the
final verifier against that exact directory, and pass its in-project report as
`--cad-verification-path`; the finalizer rejects a report outside the declared
project before the host spends another isolated verification.

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

Create and inspect both required exact-product presentation renders before
finalizing:

- `<cad-project>/snap/iso.png` is the chromatic hero, at least 800×800 px;
- `<cad-project>/snap/signature.png` is a chromatic signature-experience sheet,
  at least 1200×800 px, showing two to five exact STL poses or views that make
  the promised interaction, reveal, or anti-generic detail legible without its
  title.

Use the CAD skill's `scripts/render_product` on an exact verified STL, or
another deterministic renderer that writes those exact paths. Choose a palette,
views, and poses that expose the form and play affordance. If a reader cannot
identify the signature experience from the sheet alone, repair the geometry;
copy cannot substitute for missing product magic. Binary silhouettes from
`image-to-cad/render_views.py` are measurement evidence, not product renders;
keep them in a clearly named review/evidence directory. The finalizer rejects
missing, grayscale, flat, or undersized presentation images, and the public
snapshot preserves this explicit `snap/` render family.

The signature sheet is outcome evidence, not a turntable. Its first panel must
make the held object itself readable without copy. Remaining panels show the
exact promised states: before/action/after for a mechanism, exact projections
for a shadow or optical reveal, or setup/choice/result for a rules toy. Repeated
camera angles that do not reveal the promise do not satisfy this requirement.

Once the candidate exists, give one bounded independent native visual critic
only `snap/iso.png` and `snap/signature.png`. Use exactly one critic and at most
two total review rounds: the initial blind review and, only after a failed first
read, one focused blind rereview. Do **not** reveal the Wish, title,
concept, desired nouns, Inventor, or intended answer. First ask what physical
object it sees; which subjects it identifies; what action occurs; what spatial
or causal relationship connects those subjects; what volumetric form,
cross-section, and surface language it sees; and whether it looks like a
desirable finished product rather than a flat cutout, generic primitive,
technical test, or repeated turntable. Preserve those unprompted reads. Only
then reveal the Wish and exact compact Invented concept to that same critic.
Require the critic—not the root Manager—to compare the blind form, subjects,
action, relationship, and concept's anti-generic signature separately with the
exact promise. Sharing nouns is not enough: `beside` does not satisfy
`through`, a static fish does not satisfy a leaping whale, and a turntable does
not satisfy a state change. A constant extrusion does not satisfy a promised
pillow-rounded cabochon merely because its front silhouette uses the right
nouns.

If any form, subject, action, relationship, or anti-generic signature does not
match, or the product does not look finished and desirable, repair the single largest geometry/composition
defect, rerender both exact images, and request the one permitted focused blind
rereview. Do not coordinate a third critic or review round. Do not proceed to
the integrated final verifier or Release on copy alone. If the first candidate
passes, do not invent a repair merely to create activity.

Preserve the final review as canonical JSON at
`<cad-project>/snap/SIGNATURE-REVIEW.json` with exactly these fields:

```json
{
  "schema_version": 4,
  "kind": "autonomous-workshop.signature-experience-review",
  "concept_sha256": "<exact canonical Invented concept hash>",
  "iso_sha256": "<lowercase SHA-256 of final iso.png>",
  "signature_sha256": "<lowercase SHA-256 of final signature.png>",
  "reviewer": "<bounded independent reviewer identity>",
  "blind_held_read": "<what the reviewer saw before learning the Wish>",
  "blind_form_read": "<volumetric form, cross-section, and surface language seen blindly>",
  "blind_subjects_read": "<subjects seen before learning the Wish>",
  "blind_action_read": "<action or transformation seen before learning the Wish>",
  "blind_relationship_read": "<spatial or causal relationship seen before learning the Wish>",
  "anti_generic_signature_read": "<exact distinctive concept feature visible after reveal>",
  "wish_revealed_after_blind_read": true,
  "held_object_unmistakable": true,
  "form_matches_wish": true,
  "subjects_match_wish": true,
  "action_matches_wish": true,
  "relationship_matches_wish": true,
  "anti_generic_signature_visible": true,
  "signature_experience_unmistakable": true,
  "finished_product_desirable": true,
  "review_rounds": 1,
  "largest_risk": "<strongest concrete final finding>",
  "resolution": "<specific geometry, pose, or composition resolution>"
}
```

The finalizer requires every confirmation, all unprompted reads, the exact
Invented concept binding, one or two review rounds, and exact final-image hashes. This
is review evidence, not a numeric beauty score; never
claim an independent or blind review that did not occur. The public toy archive
keeps it beside the reviewed renders.

Keep the one final `snap/` family only under the declared CAD project. Do not
copy it to the product root or preserve identical presentation families in two
locations. Iteration renders stay outside the sealed product tree; the public
archive captures the one exact final family and its review.

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
