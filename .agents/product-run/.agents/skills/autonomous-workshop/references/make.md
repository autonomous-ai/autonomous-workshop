# Make contract

Motion requirements below apply only when immutable run-root
`MAKE-OPTIONS.json` enables `check_motion`; false skips motion sweeps and
required animation/review, with motion explicitly unverified. An older run
without that file retains mandatory motion verification.


Read `STAGE.json` once. It binds the sealed Wish, Invent result, selected
Inventor, exact output root, round, transition, and any host rejection. Repair
the cited bytes when a rejection exists; never resubmit unchanged work.

Create or continue one Make Goal. Its objective is the exact printable product
that satisfies the sealed concept and Wish. Its stopping condition is a
successful `make` finalizer writing `agent-outcome.json`. Only an exact
build-blocking contradiction may use the optional
`make-invent-revision-v1.md` route.

## Critical path

For Forge and Quest, trust the sealed Invent contract. Do not repeat research,
roster comparison, or broad concept exploration. For Spark, rank the complete
roster once from `STAGE.json`'s compact `inventor_discovery_index`, read only
the best three full custom-agent TOMLs, select the Inventor whose Taste owns
the hardest-to-fake magic, and write one compact source with exactly
`selected_inventor_id`, roster-covering `ranking`, `concept`, and `research`.

During a frozen deep-v8 or deep-v9 proof turn, follow the host prompt literally. Create or
continue the Make Goal immediately, then inspect the required stable
instructions, stage packet, and sealed concept in one bounded batch rather than
separate tool calls. Write source and its parent directories in the next file
edit before optional reading or help discovery. The broad CAD skill is
deliberately not applicable until the proof marker exists: the host already
supplies the complete proof interface. Do not inspect an empty product tree,
create an empty directory as separate work, or spawn an early critic. Persist
exact mechanism/relationship evidence, neutral held/signature blockout images,
and one compact root visual finding under
`<cad-project>/review/early-proof/`. The canonical independent blind critic
remains mandatory during final Make. The host-provided
`.make-proof-ready.json` marker ends only that native turn; it never advances
Make. The resumed high-reasoning turn must reuse the passing proof rather than
restart, and only then loads the broad CAD skill.

Replace the bracketed paths from `STAGE.json`; do not invoke help to rediscover
this interface or configure a cache. The host binds a private writable
`XDG_CACHE_HOME`. The proof entry defines exactly one module-scope `gen_step()`
and returns the build123d shape. Generate and render it in this order inside
one foreground tool call so no agent reasoning cycle separates the
deterministic commands:

```bash
"$WORKSHOP_PYTHON" .agents/skills/cad/scripts/gen <entry.step.py> --write
"$WORKSHOP_PYTHON" .agents/skills/cad/scripts/render_product <entry.step> \
  -o <cad-project>/review/early-proof/held.png \
  --motion-sheet <cad-project>/review/early-proof/signature.png \
  --motion-angles=-12,0,12
```

When the Wish supplies images or names an existing object, follow
[visual-reference-inspection.md](visual-reference-inspection.md) before
committing the form: prefer the sealed `wish-references/`, search for one when
the Wish names an object and attaches none, and label a text-derived
interpretation as such when neither is reachable rather than stopping the run.

STEP is the only geometry format the toolchain writes. `render_product`
tessellates the exact STEP in memory and there is no mesh export. The print
gates do the same: `check_mesh`, `check_overhang` and `check_thickness` build
each printable entry from source and measure its tessellation in the gate, so
printability is checkable again without a mesh deliverable. Call a product
print-ready only behind a passing `--print-gates` run at the nozzle the print
will use.

## Keep the session small

Every tool call re-sends the whole session, and the product budget counts that
re-sent input. A document read once is paid again on every later request, and
so is each empty poll. On 2026-09-11 one Spark Make spent 16 of its 75 tool
calls on empty polls of a running command, each re-sending 100-140k tokens.
These rules change how information is fetched, never which guidance applies.
A host turn prompt or frozen profile that narrows reading, such as an
early-proof or recovery turn, takes precedence over them.

- Do not re-read or re-slice a stable reference already in this session unless
  a compaction dropped it. Always re-read what can change: the newest
  `STAGE.json` after a resume or host rejection, your own sources, and fresh
  reports.
- `playtest.md` and `release-deliver.md` belong to later stages; Make does not
  need them.
- Learn a tool's flags from its documentation and `--help`, and a finalizer
  requirement from its error message. Open tool, `cadgen` or
  `stage_proposal.py` source only for the function a failure names when those
  do not answer. Seal each build group with `make-group` as its parts are
  ready; run the `make` finalizer only on the complete product tree. Repair
  everything a finalizer error names before rerunning it, never on unchanged
  bytes.
- Start a long command (`make_round`, `verify_project`, a multi-part `gen`, a
  state or motion sheet) with `yield_time_ms: 300000`. If it is still running,
  continue it with an empty `write_stdin` poll at `yield_time_ms: 300000`.
  The Codex 0.158.0 tool description allows an empty-poll yield from 5000 to
  300000 ms (ADR 0077). The yield is an upper bound, not a sleep: the poll
  returns the moment the command exits, so a long yield never waits longer than
  the work actually takes, and a short one only buys another full-price
  request. When an `exec` cell yields with a cell id instead of finishing,
  continue that cell with `wait` at the same large yield; `wait` at 1000 or
  10000 is the same waste as a short `write_stdin` poll.
- `1000` is not a waiting value. It appears in the `exec` pragma example
  (`// @exec: {"yield_time_ms": 10000, "max_output_tokens": 1000}`) as an
  **output** budget; copied onto a poll it is ten times worse than the 10000 ms
  default, and below the 5000 ms floor an empty poll enforces anyway. If the
  right yield is not obvious, omit `yield_time_ms` and take the default rather
  than writing a small number. Never put a `sleep` between polls. Wait for a
  child with one `wait_agent` at a long timeout (`timeout_ms: 300000`) rather
  than repeated 10-second waits.
- Keep tool output bounded: read round summaries, not full logs, and open a
  log only for the failure the summary cannot place.

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

For final Make, this reference owns the visual repair allowance and supersedes
the older one-repair wording in economics references: allow three focused
repair-and-rereview cycles after the initial independent review (four reviews
total), within the run's remaining budget. Early-proof and manual-review limits
are separate. Frozen older runs retain their materialized rules and tools.

1. For Forge and Quest, write the smallest viable parametric baseline with
   exactly one non-part combined `*.step.py` entry and one
   `part_<role>.step.py` per printable part. For Spark, start with components
   only: every distinct physical component, including the sole component of a
   one-piece object, gets its own `part_<role>.step.py`. Do not author the
   combined entry yet or hide component construction inside the assembly file.

   In Spark you author no Component (ADR 0080). Settle the component list and
   write only the shared files: `params.py` and anything under `features/`.
   Fix every interface there before you spawn a worker: each joint's peg,
   socket or collar dimensions and its position on both mating Components,
   taken from the Design Contract. A Component Worker then writes that
   Component's first `part_<id>.step.py` against those shared values. Spawn
   no Inventor or other agent to author a Component; an Inventor's optional
   design notes may inform the worker's brief, but an Inventor never runs
   `make_round`.

   When the sealed Design Contract has an `interfaces` section (ADR 0082),
   implement its Interfaces; do not invent others. A shared file is then a
   Shared Helper and holds only what two or more Components must agree on:
   Interface values, joint sections and standard profiles. A Component's own
   geometry, print stance and dimensions stay in its own file, even when one
   other Component must clear it: a separable Interface's Keep-out Envelope
   is that agreement. Before choosing a joint, fit, clearance or gear, run
   the wiki's `search` and `show` (`wiki/SKILL.md`), and next to each value
   name the page it came from and add that page's `assert`. Take every gear,
   bearing, fastener and other standard element from
   `.agents/skills/cad/scripts/stdpart` (`bd_warehouse`, `py_gearworks`);
   never hand-write an involute.

   Then build a sample of each Shared Helper under `samples/<name>.step.py`,
   for example a peg in its socket or a pinion on its sector. A sample
   imports the Shared Helpers from the project (`import params`, `from
   features.joints import ...`) and returns one printable piece. Run:

   ```bash
   "$WORKSHOP_PYTHON" .agents/skills/make-round/scripts/make_round <cad-project> \
     --shared-helpers
   ```

   It builds every sample and runs both print gates on it; a pass freezes
   the Shared Helpers by hash. Component rounds refuse to start before that
   freeze, so spawn no worker until it passes. Repair a failing sample in
   the Shared Helper, never in a worker's file.
2. For Spark, review and repair every component separately before assembly.
   For each `part_<role>.step.py`, run:

   ```bash
   "$WORKSHOP_PYTHON" .agents/skills/make-round/scripts/make_round <cad-project> \
     --component part_<role>.step.py
   ```

   A component passes on three things: it builds, its print gates pass, and
   an independent reviewer agrees it looks like its reference (ADR 0076). Do
   not use `--record-visual` for a component.

   Only a `component-worker` runs a component round (ADR 0080). A Workshop
   hook refuses the command above from you or any other agent, and passes
   each worker call a one-time nonce that the round records. The host refuses
   Make output holding a component round without a nonce it issued to a
   worker for that Component, so do not run one another way (for example
   through `python -c`); it will only have to be rerun.

   Delegate each Component's authoring and loop (ADR 0077, ADR 0080). Once the
   shared files are written, spawn one worker per Component, in parallel, as
   a `component-worker` agent. Give it only: the component id and the
   `part_<id>.step.py` path it writes; the shared files it builds on; its
   sealed `geometry:<id>` reference and declared camera; only that
   Component's Design Contract rows; the nozzle; and the shape-repair limit
   (5). The worker writes the first draft, runs the round above until build
   and print pass, then reports in 10 lines or fewer and waits:
   `make_round` refuses to change a passing round's geometry before its
   review is recorded (ADR 0081). The worker may view its
   own sealed reference image once. Neither you nor a worker views a
   Component's rendered rounds (front, top, iso and `compare-NN.png`); only its
   reviewer does, and the worker acts on the reviewer's text. If the runtime
   refuses a spawn at its thread limit, spawn the next worker when one
   finishes.

   When a worker reports build and print passing, you, not the worker, ask the
   reviewer. Each Component has one reviewer: spawn it once as a
   `component-reviewer` agent and send every later review of that Component
   to the same thread as a follow-up, so its cached prefix survives. Never
   spawn a second reviewer for a Component.

   The review request has one fixed shape and nothing else: the round's
   `visual-packet.json` path, its packet sha256 from the worker's report, and
   that Component's contract rows. Add no notes, no accepted differences and
   no explanation of the renders; the reviewer's definition already explains
   the print stance and the printing limits. Ask once per packet: never ask
   for a re-review of the same packet, and never edit, filter or summarize
   the answer.

   Write its answer unchanged as
   `{"round", "packet_sha256", "reviewer", "agrees", "reason", "differences"}`;
   `differences` lists `{"feature", "reference", "model"}` (at most 12) and is
   required when it disagrees. `reviewer` is the reviewer's native agent id,
   exactly as the runtime returned it when you spawned it (on Claude Code, 17
   lowercase hex characters), never a name. Record it with the same
   `--component` argument plus `--record-review <review.json>`. The
   Component's first review binds that id; `make_round` refuses a review
   naming another id and tells you the bound one. The host refuses Make output
   whose recorded review names an agent that is not this run's Component
   Reviewer or that did not read every image of the packet it judged.

   After recording, tell the worker only "review recorded for round N". The
   worker reads the recorded review from that round itself; on a
   disagreement it is the repair list for the next shape round. Keep every
   worker's thread until the assembly passes (ADR 0082), and send each later
   unlock to the worker that already holds that Component.

   Workers never edit a shared file such as `params.py` or
   `features/forms.py`; they ask you. Edit it yourself, then send back
   through its worker only each Component whose summary lists that file
   under `imported_helpers`: a change to a Shared Helper a Component does not
   import stales nothing of it (ADR 0081). The edit unlocks those Components.
   A rerun that rebuilds the reviewed B-rep keeps its review and locks again;
   one whose B-rep moved needs a new review, without spending a shape round.
   Once frozen, change a Shared Helper only when it must change, and rerun
   `--shared-helpers` at once to re-freeze it; a component round's `frozen`
   line names any frozen file that changed and every Component that imports
   it.

   Give each worker the rows of every Interface its Component joins. A
   Component in a separable or coupled Interface defines `assembly_pose(shape,
   pose)`, which places it in assembly coordinates. Its own round checks a
   separable Interface's Keep-out Envelope (the `keep` line): the inside
   Component stays inside in every declared pose, the outside one stays out.

   Check each Coupled Interface (a gear mesh, a cam, a linkage, parts that
   pass through one space at different times) once every Component it joins
   is locked:

   ```bash
   "$WORKSHOP_PYTHON" .agents/skills/make-round/scripts/make_round <cad-project> \
     --interface <interface-id>
   ```

   It refuses while a Component it joins is not locked at its current
   geometry, and runs the coupled motion check on just those Components over
   the sealed pose table. On a failure it unlocks the contract's yielding
   Component and names it; send that worker only the interface round's path.
   The worker's repair is not a shape round; after the repaired Component is
   reviewed and locked again, rerun the check. Only you run
   `--shared-helpers` and `--interface`; the hook refuses both to workers.

   When two Design Contract statements cannot both hold, for example two
   Components that print on a mating face that also carries a peg, stop and
   return a `waiting` need that quotes both statements (`SKILL.md`). Do not
   choose between them.
   A freedom the contract explicitly grants stays yours to decide.

   Use explicit `--ref` only when a reference depicts that
   component by itself; motion checks belong to the assembled object. A pass
   is component-specific evidence, not permission to skip the combined
   review. In Contract Mode (ADR 0074) name each component file after its
   Unique Geometry id, `part_<id>.step.py`: its round then shows the sealed
   `geometry:<id>` image automatically. Each `compare-NN.png` is a reference
   beside the model rendered at that reference's declared camera (`@AZ,EL` on
   the `--ref`, else the front view), both at one height. The reviewer
   compares form there: thinner or blockier bodies, missing openings, merged
   or missing members, simplified detail. No silhouette score is computed. The assembly round
   never shows a component image against the whole object; one with no
   current component pass fails there as missing. Outside Contract Mode, show
   a sealed Wish reference that depicts one component in that component's
   round with `--ref LABEL=wish-references/<file>`.

   Read each round summary's `shape` and `lock` lines (ADR 0081). A round
   that passed build and print is reviewed before its geometry may change;
   only an unchanged rerun may run first. A shape round is the first
   geometry-changing round after a disagreeing review; build and print
   repairs, unchanged reruns and changes forced by a Shared Helper or an
   assembly round are not. A Component gets five. An agreeing review locks
   the Component; so does a disagreeing review once the five are used, which
   is recorded as a component acceptance. Every acceptance is reported to the
   person when the run ends; it is never recorded as the person's decision.
   A locked Component's geometry changes only when a Shared Helper it imports
   changes or you record an assembly unlock.
3. Only after every component passes, author the non-part combined `*.step.py`
   entry and begin assembled-object rounds with:

   ```bash
   "$WORKSHOP_PYTHON" .agents/skills/make-round/scripts/make_round <cad-project> \
     --require-component-passes
   ```

   This refuses assembly review when a component has no passing isolated round
   or its freshly built STEP changed afterward, and, under an Interfaces
   section, when a Coupled Interface has no current passing `--interface`
   check. If an assembly repair
   changes a component, first record why: cite the assembly round and the
   finding you recorded there with `--record-visual`,
   `{"assembly_round", "finding", "reason"}`, and run the same `--component`
   argument plus `--record-unlock <unlock.json>`. It builds nothing. Then send
   the Component back through its worker for its isolated review-and-fix
   loop, and return to the assembled object. Forge and Quest retain their existing
   whole-product baseline sequence.
4. Generate explicit source targets with
   `.agents/skills/cad/scripts/gen <entry.step.py> --write`, which writes the
   sibling `.step`. That STEP is the only geometry artifact.
5. Run `make_round` after each source repair and inspect its exact visual packet.
   The Manager records misplaced, missing or extra parts, size/proportion
   mismatches, visible intersections, and form defects with image evidence and
   a concrete repair using `--record-visual` on the assembly round. Inspect the
   actual views and every `compare-NN.png`, even when no reference image exists. Pending or inconclusive visual
   feedback is not a pass. These self-checks do not replace independent review.
   Run only additional narrow checks affected by an edit. `make_round` gates
   every part that builds with `check_thickness` and `check_overhang` at the
   fixed 0.4 mm nozzle standard, so a wall or overhang defect surfaces in the
   round that caused it rather than at final verification.
6. Render the exact STEP to `<cad-project>/snap/iso.png` (at least 800×800 RGB)
   and `<cad-project>/snap/signature.png` (at least 1200×800 RGB). When the
   promise changes product geometry or state, generate distinct exact-state
   STEPs and use `render_product --state-sheet ... --state-source ...` at one
   fixed view. `--motion-sheet` rotates one unchanged shape and is only presentation
   viewpoint evidence; it can never prove a state transition. The signature
   sheet must show the promised states or interaction, not repeated angles.
7. For a moving mechanism, also produce and review exact-state animation using
   [motion review](motion-review-v1.md); still images cannot establish motion.
   Give one independent native critic only the images and that animation. Record its blind held
   object, volumetric form, subjects, action, and relationship. Then reveal the
   Wish and concept and check every positive and negative held-form constraint.
   In Contract Mode (a sealed Design Contract, ADR 0072), the host copies the
   contract's assembly-scoped requirements into `critical_form_requirements`
   at this reveal step; do not author that list. Allow up to three focused
   repairs, each followed by regenerated preflight, images and an independent
   rereview. Stop as soon as the review passes.
8. Run the integrated final verifier once. Do not use it as an iteration loop.
   Whenever the Wish has references, run it with `--image-derived`. The
   finalizer refuses a toy with sealed references unless the current final
   report ran in that mode (ADR 0072, Delivery 2); a plain final report cannot
   substitute for it, no matter how cleanly it passed. In Contract Mode the
   verifier fails unless every `geometry:<id>` image has a current component
   round that passed its checks and its independent review (ADR 0076). It
   writes `measure/component-acceptance.json` beside its report, and the
   finalizer copies every component acceptance from it into `product.json`.
   Do not author `component_acceptances` yourself.
9. Write product metadata and invoke the Make finalizer immediately.

Complete the blind signature review and, if needed, up to three focused repairs before
running the integrated final verifier once. The review must separately match the exact subjects,
action, and spatial/causal relationship; matching only nouns is a failure.
Enumerate every explicit positive and negative held-form requirement from
the Wish in the review's `critical_form_requirements`; each entry needs
exact blind visual evidence. Any visible departure from one of those
requirements belongs in `blocking_visual_defects`, not in a nonblocking
caveat. Use one critic and no more than four review rounds (initial plus three
rereviews). On rereview, record fresh image observations before comparison and
disclose that the critic already knows the Wish; do not claim naive recognition.
After the fourth failed review, preserve the failures and finalize a truthful
failed need rather than exceeding the allowance. Do not use the
full verifier as the visual iteration loop. Any geometry change after the
review invalidates the assembly-scoped read and requires a fresh blind read of
the regenerated images; copying old prose and replacing hashes is not a
review.

In Contract Mode with geometry-scoped rows (ADR 0072, issue 55), a
geometry-scoped repair has its own allowance, separate from the assembly
review's: each Unique Geometry's `geometry_blind_reads` entry records its own
`review_rounds`, one through four, exactly like the assembly review's
`review_rounds`. Repairing one Component invalidates only that Component's own
geometry-scoped requirement and blind read -- its row must rebind to the
Component's new `visual-packet.json` hash -- and only that geometry's
`review_rounds` needs to grow. A Unique Geometry nobody touched keeps the same
packet hash it always had, so its row and blind read carry forward unchanged,
at whatever `review_rounds` they were already at; do not spend a fresh blind
read on a Component the repair never changed. The assembly-scoped read has no
such per-Component binding, so any geometry change still invalidates it and
still needs a fresh blind read of the regenerated iso/signature images.

Do not manually delete `__cadgen__` or use `--fresh` inside the product
sandbox. The trusted host owns the isolated fresh rebuild. The finalizer safely
removes ordinary derived-cache files before hashing. If the sandbox protects a
now-empty cache directory from removal, leave it in place: byte-free
directories are ignored by both the finalizer and host gate, so never report an
empty cache directory as a blocker. Keep temporary work, transcripts, and
duplicate render families outside the sealed product tree.

## Required final product

Leave the tree at the exact `product_root` from `STAGE.json`. It contains:

- the exact nonempty root files named by `STAGE.json.required_root_files`:
  `product.json`, `assembled.step`, and `assembled.step.json`;
- for a combined model whose `assembled.step.json` (the cadgen
  assembly-package) lists two or more occurrences, one production solid per
  occurrence at `parts/<occurrence-name>.step`, one solid each, named exactly
  as the package names the occurrence (`STAGE.json.production_parts_rule`).
  The host rejects a multi-part Make without them. The shop receives these
  files as its addressable parts and renders each in the colour sealed on it;
- an occurrence name ending in the filament colour that part prints in, for
  every occurrence of a multi-part model: `<part>_<colour>`, as in `arm_black`,
  `leg_dark_brown`, `canopy_misty_blue`. Name the assembly labels that way in
  the CAD source (`asm.add(..., label=...)`) so the regenerated
  `assembled.step`, its package, and each `parts/<occurrence-name>.step` all
  carry the name. The part half before the colour must not be empty — `black`
  alone names no part. The colour has to be one the shop stocks: `beige`,
  `black`, `blue`, `cocoa_brown`, `cyan`, `dark_beige`, `dark_brown`,
  `dark_gray`, `gray`, `green`, `misty_blue`, `navy_blue`, `orange`,
  `pine_green`, `red`, `reflex_blue`, `sunflower_yellow`, `white`, `yellow`.
  That list is the filament palette the CAD skill stocks
  (`cad/scripts/cadfilament.py`, Bambu Lab PLA Lite and PETG Basic); a colour
  outside it is a spool nobody can load, and the host rejects it. The name is
  what whoever loads the printer reads the spool off, so it travels with the
  file — pick the colour first, then name the part;
- a surface colour on every leaf part of a multi-part model, authored as
  `Color(r, g, b)` with channels 0..1 taken directly from the sRGB hex you want
  the shop to show (`Color(0.82, 0.51, 0.18)` shows as `#d1822e`). Do not
  pre-convert channels to linear; the STEP, the GLB, the host renders, and the
  listing all read the sealed channels as sRGB;
- `product.json` with nonempty `title` and `summary` strings. Both are
  customer copy that reaches the shop unchanged: the title is a sayable name
  of one to four words with no dimensions, part counts, or sentences, and
  neither may use Workshop vocabulary (Wish, Taste, Goal, Make, Release,
  Playtest, Spark, Forge, Quest, artifact, gate);
- the self-contained CAD project, source, generated STEP, measurements, the
  passing `measure/thickness-<role>.md` and `measure/overhang-<role>.md`
  reports for every printable part, and final
  `measure/verification-pipeline.md`;
- one canonical final render family under `<cad-project>/snap/`;
- `<cad-project>/snap/SIGNATURE-REVIEW.json` bound to the exact concept,
  images, and print-gate reports.

The root `assembled.*` files are sealed delivery copies of the final combined
CAD output. They do not replace the self-contained CAD project or its isolated
verification. Before finalizing, confirm every packet-named root file exists as
a nonempty regular file; a nested combined export alone is not publishable.

The canonical schema-v8 review contains exactly: `schema_version`, `kind`,
`concept_sha256`, `iso_sha256`, `signature_sha256`, `reviewer`,
`blind_held_read`, `blind_form_read`, `blind_subjects_read`,
`blind_action_read`, `blind_relationship_read`,
`anti_generic_signature_read`, `wish_revealed_after_blind_read`,
`held_object_unmistakable`, `form_matches_wish`, `subjects_match_wish`,
`action_matches_wish`, `relationship_matches_wish`,
`anti_generic_signature_visible`, `signature_experience_unmistakable`,
`finished_product_desirable`, `review_rounds`, `critical_form_requirements`,
`blocking_visual_defects`, `print_gate_sha256s`, `largest_risk`, and
`resolution`. Use kind `autonomous-workshop.signature-experience-review`.
`print_gate_sha256s` maps each cited `measure/<gate>-<role>.md` report, relative
to the CAD project, to its exact sha256. Bind every printable part's passing
thickness and overhang reports there and seal product status
`full-with-thickness` with `print_ready_claim: true`; leave the map empty and
seal `digitally-verified-not-print-ready` with `false` when the round did not
open the print gates, and then never call the product print-ready. The host
reruns the verifier in the tier those two declarations name, so a claim the
sealed project cannot reproduce is refused rather than downgraded.
Every boolean is true; `review_rounds` is an integer from one through four; blockers are empty; each
critical requirement has exactly `requirement`, `blind_evidence`, and
`matches: true`. Evaluate form against the actual Wish: an exposed mechanism
or a flat component is not inherently a defect. Wrong required relationships,
unresolved geometry defects, and unproved promised functions remain blockers.

In Contract Mode, seal schema-v9 instead: the same fields as v8 plus
`requirements_source`, set to `"contract"`. `critical_form_requirements` must
be exactly the sealed contract's assembly-scoped requirements, in the
contract's order and wording -- a missing, extra, reordered, or reworded row
refuses, as does the wrong `requirements_source`. Every other schema-v8 rule
still applies unchanged. Outside Contract Mode, keep sealing schema v8 exactly
as before; do not add `requirements_source` there.

Schema v9 also carries `blind_rereads`, always present and empty unless used.
When the blind read never mentions a contract requirement, ask the critic one
narrow targeted blind re-read question about the one image that bears on it
-- still blind, with no list of requirements and no intended answer revealed
-- and preserve the exact question and the critic's verbatim answer as one
entry naming the image it concerns (`"iso"`, `"signature"`, or, for a
geometry-scoped requirement, `"geometry:<id>"`). That requirement's
`blind_evidence` may then cite the preserved answer. Using this path is a
choice, not a requirement: a blind read that already covers a requirement
needs no re-read, and asking one does not excuse a requirement the images
never show.

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
  --cad-verification-path <cad-project>/measure/verification-pipeline.md
```

The verification path is the report `verify_project --report` wrote, relative
to the product root and inside the declared CAD project.

For Spark only, also pass `--source <spark-source.json>`. Do not pass it when
`STAGE.json` already contains sealed assignment and Invented inputs. Complete
the Goal and return immediately after the finalizer succeeds. The host seals
the exact submitted bytes. Forge and Quest additionally run their isolated CAD
verification; Spark accepts Make's output without repeating that verification.

Digital evidence never proves a successful print, tactile fit, durability,
comfort, discoverability, or human delight. Quest Playtest owns its separate
evidence; Spark and Forge truthfully record Playtest as not run.
