# Make contract

Read `STAGE.json` once. It binds the sealed Wish, Invent result, selected
Inventor, exact output root, round, transition, and any host rejection. Repair
the cited bytes when a rejection exists; never resubmit unchanged work.

Create or continue one Make Goal. Its objective is the exact printable product
that satisfies the sealed concept and Wish. Its stopping condition is a
successful `make` finalizer writing `agent-outcome.json`.

Motion follows run-root `MAKE-OPTIONS.json` `check_motion` (root `AGENTS.md`):
false skips motion sweeps and the required animation and motion review, with
motion explicitly unverified.

This file is written for a new Spark Make. Read one more reference, once,
only when it applies:

- Forge or Quest: [make-forge-quest.md](make-forge-quest.md).
- No run-root `MAKE-OPTIONS.json`, a Spark packet without
  `inputs.workshop_selection`, or a sealed Design Contract below schema 4:
  [make-older-runs.md](make-older-runs.md).
- A fix run (`MAKE-OPTIONS.json` has `carry_unchanged: true`): the make-round
  skill's `references/fix-runs.md`.

## Critical path

For Spark, the accepted `inputs.workshop_selection` names the Inventor. Write
one compact `--source` JSON with exactly `selected_inventor_id` and `ranking`
copied verbatim from that assignment, plus the `concept` and `research` you
author.

For Spark outside Contract Mode, obtain references and expand the sealed Wish
before writing any component source: follow
[wish expansion](wish-expansion.md) and write
`<cad-project>/WISH-EXPANSION.md` as the selected Inventor. The Wish itself is
unchanged and still decides; the expansion only settles what it leaves open.

Before committing the form, follow
[visual-reference-inspection.md](visual-reference-inspection.md): prefer the
sealed `wish-references/`, search for images of a named object or of an
original subject's anatomy and style, generate a concept view when the runtime
has a built-in image tool, and label a text-derived interpretation as such
only when none is usable rather than stopping the run.

STEP is the only geometry format the toolchain writes. `render_product` and
the print gates (`check_mesh`, `check_overhang`, `check_thickness`) build each
printable entry from source and tessellate it in memory; there is no mesh
export. Call a product print-ready only behind a passing `--print-gates` run
at the nozzle the print will use.

## Keep the session small

Every tool call re-sends the whole session, and the product budget counts that
re-sent input. A document read once is paid again on every later request, and
so is each empty poll. These rules change how information is fetched, never
which guidance applies; a host turn prompt that narrows reading takes
precedence over them.

- Do not re-read or re-slice a stable reference already in this session unless
  a compaction dropped it. Always re-read what can change: the newest
  `STAGE.json` after a resume or host rejection, your own sources, and fresh
  reports.
- `playtest.md` and `release-deliver.md` belong to later stages; Make does not
  need them.
- Learn a tool's flags from `make-round/SKILL.md` and `--help`, and a
  finalizer requirement from its error message. Open tool, `cadgen` or
  `stage_proposal.py` source only for the function a failure names when those
  do not answer. When the concept has a `build_plan`, seal each build group
  with `make-group` as its parts are ready. Run the `make` finalizer only on
  the complete product tree, and repair everything a finalizer error names
  before rerunning it, never on unchanged bytes.
- Wait for long commands and child agents exactly as root `AGENTS.md`
  ("Wait for a long command") says, on Codex and on Claude Code.
- Keep tool output bounded: read round summaries, not full logs, and open a
  log only for the failure the summary cannot place.

## Ownership

Make owns the stage inputs and output paths, independent blind review, bounded
visual repair, final product contract, and Make finalizer. The materialized
`cad` skill owns CAD planning, modeling methods, source layout, generation,
printability, geometry checks, image-derived checks, rendering mechanics, and
CAD verification; follow its applicable pipeline. Inventor guidance owns
specialist form and character judgment. The host retains stage authority.

## Pipeline

1. **Components and shared files.** Every distinct physical component,
   including the sole component of a one-piece object, gets its own
   `part_<role>.step.py`. Do not author the combined entry yet or hide
   component construction inside the assembly file.

   A component is a piece the object really separates into at a natural seam:
   a limb at its joint, a head at the neck, a weapon, an armour plate at its
   edge, the base. It is not a print half. Do not plan paired `_a`/`_b`
   halves of one form before `check_overhang` has failed on that whole piece:
   every half doubles its component rounds, puts a seam through a visible
   face, and forces thin detail thicker so each half keeps a wall. When a
   piece fails overhang, repair it in this order and stop at the first step
   that passes:

   1. Reorient the piece's print pose.
   2. Reshape the unsupported underside: a round underside becomes a keel or
      chamfer at 45 degrees or steeper, or a flat land where it meets the base
      or a hidden face. An angular section often serves the form as well.
   3. Move or add a split at a natural seam the object already has.
   4. Only then split the single form on a plane, and record in
      `GEOMETRY-NOTES.md` the overhang failure the split fixes.

   In Spark you author no Component (ADR 0080). Settle the component list and write
   only the shared files: `params.py` and anything under `features/`. Fix
   every interface there before you spawn a worker: each joint's peg, socket
   or collar dimensions and its position on both mating Components, taken
   from the Design Contract. Spawn no Inventor or other agent to author a
   Component; an Inventor's optional design notes may inform a worker's
   brief, but an Inventor never runs `make_round`.

   With the shared files, copy the printable detail library into the
   project; workers build rivets, bosses, low domes, bands, rims, pipe ribs,
   inset panels, lancet windows, grille slits and teardrop bores with it
   instead of by hand, and blunt every point, chisel, keel and rib end to a
   land one print minimum across (0.8 mm at a 0.4 mm nozzle) with its
   `blunt_tip` and `rib_end`:

   ```bash
   "$WORKSHOP_PYTHON" .agents/skills/print-details/scripts/print_details.py --install <cad-project>
   ```

   It writes `features/print_details.py`, byte for byte, so the sealed
   project builds on its own. It is a standard element, like a `stdpart`
   gear, not a design value: never edit it.

   When the sealed Design Contract has a `print` section (schema 6, ADR
   0091), install its Print Sheets the same way, before any worker starts:

   ```bash
   "$WORKSHOP_PYTHON" .agents/skills/print-details/scripts/print_details.py --install-print <cad-project> --wish WISH.json
   ```

   It writes `print/pieces.json` (the contract's print section) and copies
   the sealed print art to `print/art/`; never edit either. Tell each
   Component Worker which Print Pieces land on its geometry (`on`). Its
   round's `paper` line fails until the part carries each one's recess,
   slot, block, ball or fold face, and final verification fails until every
   hosting part does and the sheets lay out (`print/sheets/`, ADR 0091). The
   printed paper carries the art: no part models, embosses or paints it.

   When the sealed Design Contract has an `assembly_tree` (schema 7, ADR
   0092, or a schema 8 kit, ADR 0093), install its Assembly Tree too,
   before any worker starts:

   ```bash
   "$WORKSHOP_PYTHON" .agents/skills/make-round/scripts/kit_tree.py --install <cad-project> --wish WISH.json
   ```

   It writes `tree/kit.json`; never edit it. Tell each Component Worker its
   Component's Parts (`assembly_tree.components`), each printed Part's
   filament, its Bought Parts, and the steps inside it with their insertion
   directions and lead routes. Each Part is one labelled body and each
   Component file also defines `print_parts()`, every printed Part alone in
   its print stance (`make-round/references/kit-tree.md`).
   Component rounds check the steps inside each Component; your assembly
   rounds and final verification check the joins across Components, write
   `measure/tree-report.json` and the kit's Manual into `manual/`, which the
   host checks before accepting Make. Never write, edit or reword the Manual.
   Make never changes the tree. A `labelling slip` is an ordinary gate
   failure: the worker repairs it in its next component round, you in the
   next assembly round. A `TREE DEFECT` (the sealed tree itself does not hold
   together) stops the run: do not repair it or have a worker relabel around
   it; stop at once with the need the round prints (`stage_proposal.py
   --run-root . need --stage make --status waiting --reason ...`).

   When the sealed Design Contract has an `interfaces` section (ADR 0082),
   implement its Interfaces; do not invent others. A shared file is then a
   Shared Helper and holds only what two or more Components must agree on:
   Interface values, joint sections and standard profiles. A Component's own
   geometry, print stance and dimensions stay in its own file, even when one
   other Component must clear it: a separable Interface's Keep-out Envelope
   is that agreement. Before choosing a joint, fit, clearance or gear, run
   the wiki's `search` and `show` (`wiki/SKILL.md`), and next to each value
   name the page it came from as `# wiki: <slug>` and add that page's
   `assert` naming the value. Take every gear, bearing, fastener and other
   standard element from `.agents/skills/cad/scripts/stdpart`
   (`bd_warehouse`, `py_gearworks`); never hand-write an involute.

   Then build a sample of each Shared Helper under `samples/<name>.step.py`
   (a peg in its socket, a pinion on its sector) and run `make_round
   <cad-project> --shared-helpers`. A pass freezes the Shared Helpers by
   hash; component rounds refuse to start before it, so spawn no worker
   until it passes. Repair a failing sample in the Shared Helper, never in a
   worker's file.

2. **Component Workers and Component Reviewers.** A component passes when
   it builds, its print gates pass and its independent Component Reviewer
   agrees it looks like its reference (ADR 0076). Only a `component-worker`
   runs a component round, `make_round <cad-project> --component
   part_<id>.step.py` (ADR 0080): a Workshop hook refuses it from you or any other agent and passes each
   worker call a one-time nonce, and the host refuses Make output holding a
   component round without one, so never run one another way.

   Delegate each Component's authoring and loop (ADR 0077, ADR 0080). Once
   the shared files are frozen, spawn one worker per Component, in parallel,
   as a `component-worker` agent. Give it only: the component id and the
   `part_<id>.step.py` path it writes; the shared files it builds
   on, including `features/print_details.py`; its sealed `geometry:<id>`
   reference and declared camera; only that Component's Design Contract
   rows; the rows and text of every Interface its Component joins, and which
   instances (`wing#1`, `wing#2`) they name; under a schema 8 Design
   Contract (ADR 0093) the prose sections its geometry's `prose_sections`
   names, copied verbatim from the sealed contract's `prose` (its rows win
   where they differ; never send prose to its reviewer); every Guide Image
   the contract seals that names no `geometries` or names this Component,
   by path with what it `shows`; the nozzle; and the shape-repair limit (5).
   Each component round's `summary.json` repeats the rows, Interface text
   and prose under `contract`. The worker writes the first draft, runs its
   round until build and print pass, then reports in 10 lines or fewer and
   waits. The worker may view its own sealed reference image once. Neither
   you nor a worker views a Component's rendered rounds (`sheet.png`, front,
   top, iso, `compare-NN.png`); only its reviewer does. If the runtime refuses a spawn at its thread limit,
   spawn the next worker when one finishes. Keep every worker's thread until
   the assembly passes (ADR 0082), and send each later rerun or unlock to
   the worker that already holds that Component.

   When a worker reports build and print passing, you, not the worker, ask
   the reviewer. Each Component has one reviewer: spawn it once as a
   `component-reviewer` agent and send every later review of that Component
   to the same thread, so its cached prefix survives. Never spawn a second
   reviewer for a Component. The review request has one fixed shape and
   nothing else: the round's `visual-packet.json` path and its packet sha256
   from the worker's report. `make_round` writes the Component's contract
   into the packet itself (its rows and Interface text), with the rulings
   that bind the reviewer. Ask once per packet, never for a re-review of the
   same packet, and never edit, filter or summarize the answer.

   Record the answer unchanged with `--component part_<id>.step.py
   --record-review <review.json>`; its JSON, its verdicts, Reference
   Conflicts, Ruling Disputes and refusals are in `make-round/SKILL.md`
   ("Review a component round"). `reviewer` is the reviewer's native agent
   id exactly as the runtime returned it when you spawned it (on Claude
   Code, 17 lowercase hex characters), never a name; the Component's first
   review binds it, and the host refuses Make output whose review names an
   agent that is not this run's Component Reviewer or did not read every
   image of its packet. A reviewer's `reference_conflicts` (the image shows
   what the contract forbids; the contract wins) and `ruling_disputes` (it
   thinks one of your rulings wrong) are not differences: a Reference
   Conflict is not a difference, costs no shape round, and never reaches the
   worker; it is reported when the run ends. Never repair toward the image
   and never stop the run for it. If a Ruling Dispute shows the ruling was
   wrong, answer through a Contract Amendment or a need, never by telling the
   worker to repair toward it. If `--record-review` refuses an answer as
   malformed, send the refusal line unchanged to the same reviewer thread
   and record its corrected answer for the same packet. If it refuses because
   you decided a Blocked Report of that Component after the round was
   rendered, ask the worker to rerun its Component unchanged and send the new
   packet; that rerun is not a shape round. After recording, tell the worker
   only "review recorded for round N": it reads `review.json` in that round,
   and a disagreement is its repair list for the next shape round.

   The reviewer may instead answer camera mismatch (schema 3 and later, ADR
   0083): the side of the model facing the reference's Reference Camera is
   not the side the reference shows. Record it the same way. It is not a
   disagreement and not a shape round: tell the worker nothing. Stop the run
   at once with the summary's `need:` line, quoted unchanged
   (`stage_proposal.py --run-root . need --stage make --status waiting
   --reason "<the need line>"`). Do not correct the camera, the reference or
   the model. After the host amends that one camera
   (`CONTRACT-AMENDMENTS.json` beside `WISH.json`), ask the worker to rerun
   unchanged and send that packet to the same reviewer.

   Never end your turn while a Component Worker or a Component Reviewer
   request is still running, or while a Blocked Report is open. On Claude
   Code and on Codex, wait for it exactly as root `AGENTS.md` says.

   Workers never edit a shared file; they ask you. Edit it yourself, then
   send back through its worker only each Component whose summary lists that
   file under `imported_helpers` (ADR 0081). A rerun that rebuilds the
   reviewed B-rep keeps its review and locks again; one whose B-rep moved
   needs a new review, without spending a shape round. Once frozen, change a
   Shared Helper only when it must change, and rerun `--shared-helpers` at
   once to re-freeze it.

   Every Component a separable or coupled Interface joins defines
   `assembly_pose(shape, pose)`; from schema 3 every Component defines it and
   `assembly_pose(shape, None)` is its Display Pose (ADR 0083), which its
   round shows beside each reference at that reference's camera. Its own
   round checks a separable Interface's Keep-out Envelope (the `keep` line).
   One worker builds every instance of a geometry whose count is above 1 in
   its one file (`make-round/SKILL.md`, "Instances"). Check each Coupled
   Interface once every Component it joins is locked, with `make_round
   <cad-project> --interface <interface-id>`; on a failure it unlocks the
   contract's yielding Component and names it: send that worker only the
   interface round's path. Its repair is not a shape round; rerun the check
   after the Component is locked again. Only you run `--shared-helpers` and
   `--interface`.

   For Spark with more than one Component, preview the whole object once
   (ADR 0087) when every worker has reported its first passing round, before
   you ask any reviewer: author the non-part combined `*.step.py` entry that
   places the Components and run `make_round <cad-project>
   --preview-assembly`. Open its `sheet.png` once and judge silhouette,
   stance and shape language, then the proportion, scale and placement
   between parts. Fix placement in the combined entry now. A size that comes
   from a shared value is yours to fix in `params.py`, then rerun
   `--shared-helpers`; a size inside one Component is not, because a passing
   round may not change before its review. Preview again only after a
   Component's size or placement changes, never after every round. A preview
   is evidence only: not a round, not a pass, and no substitute for the gated
   assembly review.

   Read each round summary's `shape` and `lock` lines; the round policy (ADR
   0081) is in `make-round/SKILL.md`. A passing round is reviewed before its
   geometry may change, a Component gets five shape rounds, and an agreeing
   review, or a disagreeing one once the five are used (a component
   acceptance, reported when the run ends and never recorded as the
   person's decision), locks it.

   In Contract Mode name each component file after its Unique Geometry id,
   `part_<id>.step.py`: its round then shows the sealed `geometry:<id>` image
   automatically, and the assembly round never shows it against the whole
   object. Outside Contract Mode, show a sealed Wish reference that depicts
   one component in that component's round with `--ref
   LABEL=wish-references/<file>`, and use `--ref` only when a reference
   depicts that component by itself; motion checks belong to the assembled
   object.

3. **Contract Contradictions, Blocked Reports and Contract Amendments.**
   When two Design Contract statements cannot both hold, for example two
   Components that print on a mating face that also carries a peg, stop and
   return a `waiting` need that quotes both statements (`SKILL.md`), unless
   its smallest fix is invisible and a Contract Reviewer confirms it as a
   Contract Amendment (below). Do not choose between them. A print rule the
   contract states (the stance, "no part needs support") is a statement too.
   A freedom the contract explicitly grants stays yours to decide.

   A blocked worker records a Blocked Report (issue #88) before it reports
   blocked. The same tool works on Codex and on Claude Code. Every report
   is yours to clear, at once and only with `make_round <cad-project>
   --clear-blocked <answer.json>`:

   - **Decision**, `{"report": N, "decision": "<ruling>"}`: a ruling inside
     a freedom the contract grants. Send it to that worker unchanged; it
     answers with a new round or a new report. The ruling also binds the
     Component Reviewer (issue #97) through every later packet of that
     Component, so never add it to a review request yourself. When it rules out a repair a
     review asked for, say what the reviewer may no longer ask for and why.
   - **Decision waiting on a Component**, `{"report": N, "decision":
     "<ruling>", "waits_on": "part_<other>.step.py"}`: send that Component's
     worker the change. The
     report stays open until that Component's next passing round, whose
     summary has a `wake` line; then clear it with a new decision for the
     blocked worker. Never leave a woken worker idle.
   - **Contract Contradiction**, `{"report": N, "need": "<one line quoting
     every row of the report>"}`: seal the printed need at once with
     `stage_proposal.py --run-root . need --stage make --status waiting
     --reason "<the need>"`.
   - **Contract Amendment**, `{"report": N, "amendment": M}`: amendment M,
     proposed with `"report": N`, was applied. Tell the worker its rows
     changed and to rerun.

   Do not answer a blocked worker in prose alone. While any report is open
   or waiting, `make_round` refuses an assembly round and `--full`, the
   finalizer refuses the Make proposal, and the host refuses Make acceptance.
   On Claude Code the host also refuses your turn end unless it ends on a
   recorded need. After a compaction run `make_round <cad-project>
   --blocked-reports`.

   **Contract Amendments (ADR 0085).** Before you turn a Contract
   Contradiction into a need, ask whether its smallest fix changes anything a
   sealed reference image shows. A clearance, a print stance, a hidden face
   or a value no image shows does not; an outline, a proportion, a member or
   a visible feature does. Only an invisible fix may be amended inside the
   run:

   1. Write `{"rows": ["<statement>", "<statement>"], "changes": [{"from":
      "<the whole requirement or Interface text, verbatim>", "to": "<its new
      text>"}], "reason": "<why the rows cannot both hold and why this is the
      smallest fix>", "report": N}` (leave out `report` when no Blocked
      Report names the rows) and run `make_round <cad-project>
      --propose-amendment <proposal.json>`. Change only requirement and
      Interface text.
   2. Spawn a **fresh** `contract-reviewer` (never a Component Reviewer,
      never one that reviewed an earlier amendment) and send it exactly:
      the packet path and its sha256, nothing else.
   3. Record its JSON answer unchanged, adding `amendment`, `packet_sha256`
      and `reviewer`, with `make_round <cad-project>
      --record-amendment-review <review.json>`. Keep its `guides_wrong`
      unchanged when the packet lists `guides`; the run reports them. On
      Claude Code `reviewer` is the agent id the runtime returned when you
      spawned it, and the host checks it started as a `contract-reviewer`
      and read every sealed reference. On Codex it is the name you gave the
      reviewer thread.
   4. Applied, the tool names the Components whose rows changed: they unlock
      and their next rounds read the amended rows; tell each one's worker.
      Refused with the contradiction confirmed, nothing visible and
      `smallest: false`, you get **one Smaller Retry**: the same rows, each
      `to` its row's `from` with only words deleted, sent to another
      **fresh** `contract-reviewer`, never the one who refused. The tool
      refuses a retry that adds text, a third proposal for the same rows, and
      a retry after any other refusal. Any other refusal or a refused retry
      stops the run on the need the tool prints; clear the report with it, if
      any, and seal it at once. A visible change always stops the run with a
      need.

   Never change a row any other way and never resolve a contradiction
   silently in shared code. While an amendment awaits review, assembly
   rounds, `--full` and the Make proposal are refused. After a compaction
   run `make_round <cad-project> --contract-amendments`.

   **Owner Contract Amendments (issue #100).** After every resume from a
   Contract Contradiction need, run `make_round <cad-project>
   --contract-amendments`. An `owner amendment` lists each changed row
   before and after and the Components it unlocks; when the run root's
   `CONTRACT-AMENDMENTS.json` holds an `objective`, it replaces
   `WISH.json`'s. Ask each unlocked Component's worker to rerun, send the new
   packet to its reviewer, and continue; an owner's assembly row binds no
   Component. From then on `--propose-amendment` is refused: a further
   contradiction stops the run on a need.

4. **Assembly rounds.** Only after every component passes, begin
   assembled-object rounds on the non-part combined `*.step.py` entry
   (author it now if no preview did) with `make_round <cad-project>
   --require-component-passes`. It refuses assembly review when a component
   has no passing isolated round, its freshly built STEP changed afterward,
   or a Coupled Interface has no current passing `--interface` check. Every
   assembly round also runs `inspect interfere` on the entry; its `clash`
   line names each pair of Components that interpenetrate where they are
   placed, and any clash, or an entry that cannot build its parts through
   cadgen, fails the round. Fix that before the blind review is spent.

   On each assembly round open `sheet.png` once and judge silhouette and
   stance first, then proportion between parts, then whether surface detail
   reads, and every `compare-NN.png`. Record `matches_plan`,
   `matches_reference` (null without references) and findings with
   `--record-visual` (`make-round/SKILL.md`, "Record assembly visual
   feedback"). A wrong silhouette is usually repaired by a different
   construction family, not by parameter nudges. Pending or inconclusive
   feedback is not a pass, and it does not replace the independent review.
   If an assembly repair changes a component, first record why with
   `--component part_<id>.step.py --record-unlock <unlock.json>`,
   `{"assembly_round", "finding", "reason"}`, citing a finding recorded on
   that assembly round; then send the Component back through its worker and
   reviewer, and return to the assembled object.

5. **Signature images.** Generate explicit source targets with
   `.agents/skills/cad/scripts/gen <entry.step.py> --write`; that STEP is the
   only geometry artifact. Render the exact STEP to `<cad-project>/snap/iso.png`
   (at least 800×800 RGB) and `<cad-project>/snap/signature.png` (at least
   1200×800 RGB). When the promise changes product geometry or state,
   generate distinct exact-state STEPs and use `render_product --state-sheet
   ... --state-source ...` at one fixed view. `--motion-sheet` rotates one
   unchanged shape and is only presentation viewpoint evidence; it can never
   prove a state transition. The signature sheet must show the promised
   states or interaction, not repeated angles. For a moving mechanism with
   motion enabled, also produce and review exact-state animation using
   [motion review](motion-review-v1.md).

6. **Blind review** (below), then **final verification**: run the integrated
   final verifier once, never as an iteration loop. Whenever the Wish has
   references, run it with `--image-derived`; the finalizer refuses a toy
   with sealed references unless the current final report ran in that mode.
   In Contract Mode the verifier fails unless every `geometry:<id>` image has
   a current component round that passed its checks and its independent
   review (ADR 0076). It writes `measure/component-acceptance.json` beside
   its report, and the finalizer copies every component acceptance from it
   into `product.json`; do not author `component_acceptances` yourself.

   **Guide Images (ADR 0089).** Open each sealed Guide Image
   (`wish-references/guide-NN-<slug>`) before you write the shared files and
   joints, and use it to plan how the Components meet and move. Nothing
   compares a Guide Image with the model, and where it disagrees with the
   contract, the contract wins. Before the final verifier, write
   `<cad-project>/guide-steps.json`: `{"guides": [{"file":
   "guide-01-x.png", "steps": [{"step": "<a step exactly as the contract's
   guides[] lists it>", "checked": "<the motion state or pose you checked it
   in>"} or {"step": ..., "skipped": "<why>"}], "conflicts": [{"guide":
   "<what the guide shows>", "contract": "<what the contract requires>"}]}]}`.
   With `--check-motion true` the verifier fails until every listed step has
   one entry; it counts them and never judges them.

7. Write product metadata and invoke the Make finalizer immediately.

Do not manually delete `__cadgen__` or use `--fresh` inside the product
sandbox. The finalizer safely removes ordinary derived-cache files before
hashing; byte-free cache directories are ignored by both the finalizer and
host gate, so never report an empty cache directory as a blocker. Keep
temporary work, transcripts, and duplicate render families outside the sealed
product tree.

## Blind review

Complete the blind signature review and, if needed, up to three focused
repairs, each followed by regenerated images and an independent rereview,
before running the final verifier once. Give one independent native critic
only the images (and the animation, when there is one). Record its blind held
object, volumetric form, subjects, action, and relationship. Then reveal the
Wish and concept and check every positive and negative held-form constraint.
The review must separately match the exact subjects, action, and
spatial/causal relationship; matching only nouns is a failure.

Enumerate every explicit positive and negative held-form requirement from the
Wish in `critical_form_requirements`; each entry needs exact blind visual
evidence. In Contract Mode (ADR 0072) the host copies the contract's
assembly-scoped requirements there at the reveal step; do not author that
list. When `WISH-EXPANSION.md` exists, also enumerate its defining parts and
negative spaces; a choice the Wish does not require never fails a faithful
build. Any visible departure from one of those requirements belongs in
`blocking_visual_defects`, not in a nonblocking caveat. Use one critic and no
more than four review rounds (initial plus three rereviews). On rereview,
record fresh image observations before comparison and disclose that the critic
already knows the Wish; do not claim naive recognition. After the fourth
failed review, preserve the failures and finalize a truthful failed need.
Any geometry change after the review invalidates the assembly-scoped read and
requires a fresh blind read of the regenerated images; copying old prose and
replacing hashes is not a review.

**Geometry-scoped rows.** In Contract Mode with geometry-scoped requirements,
`geometry_form_requirements` has one row per sealed geometry row, in the
contract's order, each `{"requirement", "geometry", "blind_evidence",
"matches": true, "packet_sha256", "view": "sheet"}`. Its evidence is the
Component's own review, not the critic:

- When the Component's current passing round carries a recorded Component
  Review by its bound reviewer (`reviewer_id` in its component state) that
  agrees, or is a component acceptance, with `matches_plan` true, the row's
  `packet_sha256` is the packet that review judged (the reviewed round's
  `visual.packet_sha256`, also for a carried review) and its
  `blind_evidence` is that review's `reason`, copied verbatim. The critic
  does not read that geometry.
- Every other geometry (a runtime that cannot bind its reviewer, as on
  Codex today, an acceptance whose reviewer found the rows unmet) keeps one
  critic read in `geometry_blind_reads`, `{"geometry", "blind_read",
  "review_rounds"}`, ordered by first row, with its own one to four
  `review_rounds`, and its rows bind the current round's packet with the
  critic's evidence. Leave `geometry_blind_reads` out when no geometry needs
  one.

A row binds the Component's current passing packet, so a Component nobody
repaired keeps its row unchanged across a repair, while a repaired
Component's row must rebind. The assembly-scoped read has no such binding.

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
  `pine_green`, `red`, `reflex_blue`, `sunflower_yellow`, `white`, `yellow`
  (the CAD skill's `cad/scripts/cadfilament.py` palette); the host rejects any
  other. Pick the colour first, then name the part;
- a surface colour on every leaf part of a multi-part model, authored as
  `Color(r, g, b)` with channels 0..1 taken directly from the sRGB hex you want
  the shop to show (`Color(0.82, 0.51, 0.18)` shows as `#d1822e`). Do not
  pre-convert channels to linear;
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
CAD output. Before finalizing, confirm every packet-named root file exists as
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
open the print gates, and then never call the product print-ready. Spark's
host does not rerun the verifier (ADR 0061): the finalizer binds this review
to the passing reports and seals the final verifier's report as you wrote it,
so declare only what that `--print-gates` run showed.
Every boolean is true; `review_rounds` is an integer from one through four; blockers are empty; each
critical requirement has exactly `requirement`, `blind_evidence`, and
`matches: true`. Evaluate form against the actual Wish: an exposed mechanism
or a flat component is not inherently a defect. Wrong required relationships,
unresolved geometry defects, and unproved promised functions remain blockers.

In Contract Mode, seal schema-v9 instead: the same fields as v8 plus
`requirements_source`, set to `"contract"`, `blind_rereads`, and, when the
contract has geometry-scoped rows, `geometry_form_requirements` and any
`geometry_blind_reads` (above). `critical_form_requirements` must be exactly
the sealed contract's assembly-scoped requirements, in the contract's order
and wording -- a missing, extra, reordered, or reworded row refuses, as does
the wrong `requirements_source`. Outside Contract Mode, keep sealing schema
v8; do not add `requirements_source` there.

`blind_rereads` is always present and empty unless used. When the blind read
never mentions a contract requirement, ask the critic one narrow targeted
blind re-read question about the one image that bears on it -- still blind,
with no list of requirements and no intended answer revealed -- and preserve
the exact question and the critic's verbatim answer as one entry naming the
image it concerns (`"iso"`, `"signature"`, or `"geometry:<id>"` for a
geometry the critic reads). That requirement's `blind_evidence` may then cite
the preserved answer. A blind read that already covers a requirement needs no
re-read, and asking one does not excuse a requirement the images never show.

Separate immutable user requirements from inventor-selected styling. Before
the final review, revise nonessential naming, species, palette or styling
decisions when the result suggests a better fit; preserve the previous choice
and reason in `research.design_changes`. Keep the required function,
constraints and distinctive experience. The final concept, product and review
must agree. Never retroactively rewrite a failed review or simply change
hashes. A missing function cannot become a styling change.

Then run:

```bash
"$WORKSHOP_PYTHON" .agents/skills/autonomous-workshop/scripts/stage_proposal.py \
  --run-root . make \
  --product-root <STAGE product_root> \
  --cad-project-path <path inside product root> \
  --cad-verification-path <cad-project>/measure/verification-pipeline.md \
  --source <spark-source.json>
```

The verification path is the report `verify_project --report` wrote, relative
to the product root and inside the declared CAD project. Pass `--source` only
for Spark, never when `STAGE.json` already contains sealed assignment and
Invented inputs. Complete the Goal and return immediately after the finalizer
succeeds. The host seals the exact submitted bytes; Spark accepts Make's
output without repeating its verification.

Digital evidence never proves a successful print, tactile fit, durability,
comfort, discoverability, or human delight. Spark and Forge truthfully record
Playtest as not run.
