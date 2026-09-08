# Make contract

Read `STAGE.json` once. It binds the sealed Wish, Invent result, selected
Inventor, exact output root, round, transition, and any host rejection. Repair
the cited bytes when a rejection exists; never resubmit unchanged work.

Create or continue one Make Goal. Its objective is the exact printable product
that satisfies the sealed concept and Wish. Its stopping condition is a
successful `make` finalizer writing `agent-outcome.json`. Only an exact
build-blocking contradiction may use the optional
`make-invent-revision-v1.md` route, and only while `STAGE.json` sets
`invent_revision_allowed: true`. On the last lifecycle round the packet sets
`final_round: true` and `invent_revision_allowed: false`: a Make -> Invent
revision cannot be finalized, so either finish a conforming build from the
sealed concept or return a truthful `need`.

`inputs.vault_leads`, when present, lists what the design vault records
against the concept's mechanisms: `risk` entries with the anti-pattern, the
recorded `suggested_fixes`, banked `evidence`, and a stable `id`. They are
computed by the host from the phase's `VAULT.json` snapshot, not authored by a
model. Forge and Quest packets carry leads for the sealed Invent concept; Spark
packets carry leads derived from the mechanisms the Wish itself names. Read
them before building; a lead is a lead, not a verdict, and Make answers them
with the built product rather than a written response (Quest Playtest later
answers each lead explicitly).

## Critical path

For Forge and Quest, trust the sealed Invent contract. Do not repeat research,
roster comparison, or broad concept exploration. For Spark, rank the complete
roster once from `STAGE.json`'s compact `inventor_discovery_index`, read only
the best three full custom-agent TOMLs, select the Inventor whose Taste owns
the hardest-to-fake magic, and write one compact source with exactly
`selected_inventor_id`, roster-covering `ranking`, `concept`, and `research`.
The Spark `concept` is sealed by the same finalizer code as a Forge/Quest
Invent, so it must satisfy the complete Invented schema-5 contract in
[invent.md](invent.md): `title`, `summary`, `interaction`, `envelope_mm`,
`mechanisms` (with `novel_mechanisms` for any slug the vault does not know),
`components` with exactly the nine fields, a `build_plan`, hedge-free
quantities, and the vault rules when `VAULT.json` is materialized. Spark may
read `invent.md` for that contract even though it runs no Invent stage.

During the current deep-v13 Forge/Quest proof turn (the same exact-state
proof as v10 through v12), follow the host prompt literally. Create or continue
the Make Goal immediately, then inspect the required stable instructions, stage
packet, and sealed concept in one bounded batch rather than separate tool
calls. In the next file edit, author the shared helper
`review/early-proof/proof.py` plus three exact-state entries
`state-0.step.py`, `state-1.step.py`, and `state-2.step.py` under
`<cad-project>/review/early-proof/`, before optional reading or help discovery.
The broad CAD skill is deliberately not applicable until the proof marker
exists: the host already supplies the complete proof interface. Do not inspect
an empty product tree, create an empty directory as separate work, or spawn an
early critic. Persist the three STEP/STL states, one neutral held image, one
state sheet, and one compact `finding.json` that records what is visibly
distinct in each frame and whether the Wish's form, subjects, action, and
relationship survive. The canonical independent blind critic remains mandatory
during final Make. The host-provided `.make-proof-ready.json` marker ends only
that native turn; it never advances Make. The host accepts it only when the
helper, three state sources, three STEP files, three distinct STL files, held
image, state sheet, and finding are stable regular files at least as new as
their sources. The resumed final-Make turn must reuse the passing proof rather
than restart, and only then loads the broad CAD skill.

Replace the bracketed paths from `STAGE.json`; do not invoke help to rediscover
this interface or configure a cache. The host binds a private writable
`XDG_CACHE_HOME`. Each state entry defines exactly one module-scope `gen_step()`
and returns that state's build123d shape. Generate, export, and render in this
order inside one foreground tool call so no agent reasoning cycle separates the
deterministic commands:

```bash
for s in 0 1 2; do
  "$WORKSHOP_PYTHON" .agents/skills/cad/scripts/gen <cad-project>/review/early-proof/state-$s.step.py --write
  "$WORKSHOP_PYTHON" .agents/skills/cad/scripts/export <cad-project>/review/early-proof/state-$s.step --stl
done
"$WORKSHOP_PYTHON" .agents/skills/cad/scripts/render_product <cad-project>/review/early-proof/state-0.stl \
  -o <cad-project>/review/early-proof/held.png \
  --state-sheet <cad-project>/review/early-proof/signature.png \
  --state-stl <cad-project>/review/early-proof/state-0.stl \
  --state-stl <cad-project>/review/early-proof/state-1.stl \
  --state-stl <cad-project>/review/early-proof/state-2.stl
```

The renderer rejects visually indistinguishable state frames. `--motion-sheet`
rotates one unchanged mesh and is viewpoint evidence only; it never proves a
state transition, so it is not the proof sheet. Frozen older profiles
(deep-v8/v9 single-entry `--motion-sheet` proof, and earlier) keep the exact
commands their own materialized profile prescribes; read the materialized
`deep-economics-v<N>.md` for that run.

## Ownership and pipeline

Make owns the stage inputs and output paths, independent blind review, bounded
visual repair, final product contract, and Make finalizer. The materialized
`cad` skill owns CAD planning, modeling methods, applicable progressive
references, source layout, generation, exports, printability, geometry checks,
image-derived checks, rendering mechanics, and CAD verification. Inventor
guidance owns specialist form and character judgment. A CAD artifact or gate
named here is a required Make outcome, not a replacement for an applicable
CAD-skill step. The host retains stage authority and the final deterministic
product gate.

Follow the applicable CAD pipeline when the frozen Make profile permits loading
the skill. Existing early-proof turns keep their prescribed narrow commands and
skill deferral. This ownership split does not change their handoff or introduce
a direct Make route.

Use one product funnel:

1. Write the smallest viable parametric baseline with exactly one non-part
   combined `*.step.py` entry and one `part_<role>.step.py` per printable part.
2. Generate explicit source targets with
   `.agents/skills/cad/scripts/gen <entry.step.py> --write`. Export STL from the
   fresh STEP with `.agents/skills/cad/scripts/export <entry.step> --stl`.
   When the sealed concept carries a `build_plan` (Invented schema 5), also
   export every component to `<product_root>/parts/<component-key>.stl` in
   print orientation and seal each group; see "Build groups" below.
3. Run only narrow checks affected by an edit. Once the baseline is plausible,
   run `.agents/skills/cad/scripts/verify_project <cad-project>
   --print-preflight` without `--fresh`. It must cover every printable at the
   fixed 0.4 mm nozzle standard.
4. Render the exact STL to `<cad-project>/snap/iso.png` (at least 800×800 RGB)
   and `<cad-project>/snap/signature.png` (at least 1200×800 RGB). When the
   promise changes product geometry or state, generate distinct exact-state
   STLs and use `render_product --state-sheet ... --state-stl ...` at one fixed
   view. `--motion-sheet` rotates one unchanged mesh and is only presentation
   viewpoint evidence; it can never prove a state transition. The signature
   sheet must show the promised states or interaction, not repeated angles.
5. For a moving mechanism, also produce and review exact-state animation using
   [motion review](motion-review-v1.md); still images cannot establish motion.
   Give one independent native critic only the images and that animation. Record its blind held
   object, volumetric form, subjects, action, and relationship. Then reveal the
   Wish and concept and check every positive and negative held-form constraint.
   Make one focused repair at most and one blind rereview at most.
6. Run the integrated final verifier once. Do not use it as an iteration loop.
7. Write product metadata and invoke the Make finalizer immediately.

Complete the blind signature review and, if needed, one coherent repair before
running the integrated final verifier once. The review must separately match the exact subjects,
action, and spatial/causal relationship; matching only nouns is a failure.
Enumerate every explicit positive and negative held-form requirement from
the Wish in the review's `critical_form_requirements`; each entry needs
exact blind visual evidence. Any visible departure from one of those
requirements belongs in `blocking_visual_defects`, not in a nonblocking
caveat. Use one critic and no more than two review rounds. Do not use the
full verifier as the visual iteration loop. Any geometry change after the
review invalidates it and requires a fresh blind read of the regenerated
images; copying old prose and replacing hashes is not a review.

Do not manually delete `__cadgen__` or use `--fresh` inside the product
sandbox. The trusted host owns the isolated fresh rebuild. The finalizer safely
removes ordinary derived-cache files before hashing. If the sandbox protects a
now-empty cache directory from removal, leave it in place: byte-free
directories are ignored by both the finalizer and host gate, so never report an
empty cache directory as a blocker. Keep temporary work, transcripts, and
duplicate render families outside the sealed product tree.

## Build groups

The sealed concept's `build_plan` (Invented schema 5; concepts sealed as
schema 3 or 4 need no groups) orders its components into named groups. Make's
discipline is to work group by group: build that group's parts, export each to
`<product_root>/parts/<component-key>.stl`, run the narrow checks, satisfy the
group's `exit_criteria`, and then seal the group:

```bash
"$WORKSHOP_PYTHON" .agents/skills/autonomous-workshop/scripts/stage_proposal.py \
  --run-root . make-group --product-root <STAGE product_root> --group <group>
```

For Spark, also pass the same `--source <spark-source.json>` that the `make`
finalizer takes; the group is sealed against that authored concept's
`build_plan`. `make-group` refuses `--source` when `STAGE.json` already carries
sealed inputs, refuses a product root other than
`artifacts/make/r<round>/product`, and refuses a group name absent from the
plan. It requires a nonempty regular `parts/<key>.stl` for every part in the
group, hashes those bytes, and writes
`<product_root>/groups/<group>.json` (`schema_version` 1, kind
`autonomous-workshop.make-group`, `group`, `parts`, `files` keyed by component
key). Re-run it for a group after any change to its parts.

What the host and the `make` finalizer verify: every group in the plan has a
sealed `groups/<group>.json` whose `parts` list equals the plan and whose
`files` hashes match the current `parts/<key>.stl` bytes for every component.
Sealing order, stopping at a group that will not seal, and `exit_criteria` are
your discipline, not host-enforced checks; the host does not read
`exit_criteria`. Building later groups on an unsealed group is still the wrong
order because later groups mate with it.

## Required final product

Leave the tree at the exact `product_root` from `STAGE.json`. It contains:

- the exact nonempty root files named by `STAGE.json.required_root_files`:
  `product.json`, `assembled.step`, `assembled.step.json`, and `assembled.stl`;
- `product.json` with nonempty `title` and `summary` strings. Both are
  customer copy that reaches the shop unchanged. Enforced deterministically
  at Make and again at Release: the title is at most 300 characters, already
  stripped (no leading or trailing whitespace), contains no carriage return,
  and neither title nor summary may contain the whole words `Wish`, `Taste`,
  or `Inventor` (capitalized) or `playtest` or `finalizer` (any case).
  Guidance, not enforced: the title is a sayable name of one to four words
  with no dimensions, part counts, or sentences, and it avoids the other
  Workshop terms (Goal, Make, Release, Spark, Forge, Quest, artifact, gate)
  unless they are the ordinary customer word ("Starling Gate");
- the self-contained CAD project, source, generated STEP/STL, measurements,
  passing `measure/print-preflight.md`, and final
  `measure/verification-pipeline.md`;
- one canonical final render family under `<cad-project>/snap/`;
- `<cad-project>/snap/SIGNATURE-REVIEW.json` bound to the exact concept,
  preflight, and images.

The root `assembled.*` files are sealed delivery copies of the final combined
CAD output. They do not replace the self-contained CAD project or its isolated
verification. Before finalizing, confirm every packet-named root file exists as
a nonempty regular file; a nested combined export alone is not publishable.

The canonical schema-v6 review contains exactly: `schema_version`, `kind`,
`concept_sha256`, `iso_sha256`, `signature_sha256`, `reviewer`,
`blind_held_read`, `blind_form_read`, `blind_subjects_read`,
`blind_action_read`, `blind_relationship_read`,
`anti_generic_signature_read`, `wish_revealed_after_blind_read`,
`held_object_unmistakable`, `form_matches_wish`, `subjects_match_wish`,
`action_matches_wish`, `relationship_matches_wish`,
`anti_generic_signature_visible`, `signature_experience_unmistakable`,
`finished_product_desirable`, `review_rounds`, `critical_form_requirements`,
`blocking_visual_defects`, `print_preflight_sha256`, `largest_risk`, and
`resolution`. Use kind `autonomous-workshop.signature-experience-review`.
Every boolean is true; `review_rounds` is one or two; blockers are empty; each
critical requirement has exactly `requirement`, `blind_evidence`, and
`matches: true`. Evaluate form against the actual Wish: an exposed mechanism
or a flat component is not inherently a defect. Wrong required relationships,
unresolved geometry defects, and unproved promised functions remain blockers.

Separate immutable user requirements from inventor-selected styling. In Spark,
before the final review, revise nonessential naming, species, palette or
styling decisions when the result suggests a better fit; preserve the previous
choice and reason in `research.design_changes`. Keep the required function,
constraints and distinctive experience. The final concept, product, manual
and review must agree. Never retroactively rewrite a failed review or simply
change hashes. Forge/Quest sealed concepts still require their existing
authorized revision path. A missing function cannot become a styling change.

Then run:

```bash
"$WORKSHOP_PYTHON" .agents/skills/autonomous-workshop/scripts/stage_proposal.py \
  --run-root . make \
  --product-root <STAGE product_root> \
  --cad-project-path <path inside product root> \
  --cad-verification-path <path inside product root>
```

For Spark only, also pass `--source <spark-source.json>`. Do not pass it when
`STAGE.json` already contains sealed assignment and Invented inputs. Complete
the Goal and return immediately after the finalizer succeeds. The host then
rehashes the complete tree and reruns the authoritative isolated CAD gate.

Digital evidence never proves a successful print, tactile fit, durability,
comfort, discoverability, or human delight. Quest Playtest owns its separate
evidence; Spark and Forge truthfully record Playtest as not run.
