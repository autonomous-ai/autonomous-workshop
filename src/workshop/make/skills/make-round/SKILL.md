---
name: make-round
description: Run isolated component or assembled-object Make repair rounds with deterministic CAD checks and visual comparison. Render the selected scope beside each reference at its declared camera; an independent reviewer judges each component, the Manager records assembly findings alongside build, print and motion results. Does not replace independent blind review or final verification.
---

**Motion verification is opt-in.** Standalone `make_round` and `verify_project`
default to false; pass `--check-motion true` to enable it. Inside Workshop,
read the immutable run-root `MAKE-OPTIONS.json`: the tools inherit its
`check_motion` value and reject contradictory flags. A missing options file
in an older materialized run retains its mandatory motion policy. When false,
skip motion sweeps and required animation/reconstruction/review, even if a
manifest or assembly claims exist. Motion is unverified, never passed; do not
claim assemblability or working motion from skipped evidence. Build, fit,
print gates and still-image review remain required. These rules take
precedence over motion-specific requirements in references and templates.

**A correction carries unchanged parts forward.** This is the default for
`workshop fix`, recorded as `carry_unchanged` in the run-root
`MAKE-OPTIONS.json` under `schema_version: 2`;
`motion_policy.carry_unchanged()` reads it. It is false for every run with no
source to carry from, and for every run created before the policy existed --
those have no schema-2 document, so a refreshed tool still reads them the way
they were created. `workshop fix --full` declines it. The policy changes only
what a round may CARRY FORWARD. It lowers no threshold, relaxes no gate and
skips nothing about the assembly.

What it permits, and only after the changed-part set is established by
building EVERY part and comparing its B-rep identity against the source's
(ADR 0073 -- never STEP bytes, which an exporter can serialize differently for
an unchanged shape, and never a shape reloaded from a STEP file, which does
not hash like the one that was built):

- A part whose B-rep is identical to the source's needs no new isolated
  component round, even when its exported STEP bytes differ. The source
  archive's round history for that part is still exactly true of it, because a
  gate is a pure function of the shape it reads. Carry that history forward
  and record the B-rep hash it is carried on.
- Its per-part measure reports are carried forward the same way, unchanged.

`gen --write --json` reports each part's B-rep identity as `identitySha256`,
alongside the exact installed `build123d`/`cadquery-ocp` versions it was
computed under as `toolchainVersions`, computed on the shape it just built,
never on an import. Before finalizing a round, write
`<cad_project_path>/component-identities.json` naming, for every sealed
`.step` Component, `{"component_identities": {"<path>": "<identitySha256>",
...}, "toolchain": {"build123d": "<version>", "cadquery_ocp": "<version>"}}`
(paths relative to the product root, e.g. `cad/part_belt_cell.step`, the
`toolchainVersions` object's own keys). The Make finalizer seals this into
`made.json` as `schema_version: 2`'s `component_identities`/`toolchain`
fields -- this is what lets a later Correction Run skip rebuilding this
archive's own Components (issue #64, ADR 0073's "Update from #60"). Leave the
sidecar file unwritten for a round with no `identitySha256` to report (an
imported/committed STEP target only, or the DXF pipeline): the finalizer
seals plain `schema_version: 1`, exactly as before.

For the source side of a Correction Run's comparison: read the source
archive's `make/made.json` first. If it is `schema_version: 2` and its
`toolchain` matches this run's own installed `build123d`/`cadquery-ocp`
versions exactly, use its `component_identities[path]` directly -- no
rebuild. Otherwise (schema 1, sealed before this change, or a toolchain that
does not match -- a sealed hash from a different OCCT is not comparable),
get the source side by rebuilding the source's own `part_<role>.step.py` in a
scratch copy of its `make/` tree with the same `gen --write --json` and
reading its `identitySha256` there; the source's own generator sources and
shared helpers are already inside the revision snapshot, so this needs no new
input. There is no tolerance on this comparison: two hashes either match or
they do not.

You are not trusted on this, and do not need to be: `make_round
--require-component-passes` rebuilds every part and refuses assembly review
for any whose B-rep identity no longer matches its recorded pass. A part
whose shape moved cannot be carried even if you try -- and one whose exported
STEP merely serialized differently is no longer refused for it.

What the policy never touches:

- The hash proof itself. It is the whole warrant for everything above, so it
  is computed fresh, over every part, every time.
- `refs:assembly`, `validate:assembly` and `interfere:assembly`. The assembly
  changes whenever any part does, and interference is a property of the whole
  set, never of a part.
- Every gate on every CHANGED part, and the assembled-object rounds.
- `verify_project`, the whole-set renders and the independent blind review.
  The final sweep is what would catch a mistake in the carry-forward
  reasoning, so scoping it would remove the one check that makes the rest
  safe.

Write a `measure/quick-fix-carry.md` naming every part carried forward, the
B-rep hash it was carried on, and what was regenerated instead. A reader must be
able to tell a carried report from a fresh one without diffing, because the
round record itself cannot say which run produced it. If the changed-part set
turns out to be most of the project, say so and regenerate everything: the
policy saves nothing there and the claim is weaker.



# Make round

One Make iteration, one combined summary. A command batches the deterministic
checks and rendering; a second records the native visual inspection. This skill exists because a
Make session's cost is the number of model requests times the context each
carries: the first published wind-up microduck (2026-09-07) spent 673 shell
calls and 925 model requests, and 430 of those shell calls were `cat`, `rg`,
`sed`, and `tail` over skill sources and the run's own logs. This page is the
tool card those reads were looking for, and `make_round` is the loop those
calls were reassembling by hand.

## Rules

- Run `make_round` once per repair round, after editing source and before
  deciding what to repair next. For a component round, have an independent
  reviewer judge the visual packet and record it with `--record-review`; for
  an assembly round, inspect the packet yourself and record your findings
  with `--record-visual`. Neither rebuilds. Read its summary; open a full report only
  when the summary names a failure you cannot place.
- In a run with the make_round guard (ADR 0080), only a `component-worker`
  runs a component round; the root Workshop Manager alone runs
  `--record-review`, `--record-unlock`, `--record-visual`, assembly rounds,
  `--shared-helpers`, `--interface` (ADR 0082), `--clear-blocked`,
  `--propose-amendment` and `--record-amendment-review` (ADR 0085); only
  a worker runs `--report-blocked` (issue #88). A Workshop hook
  refuses a call from the wrong agent and gives each worker round a one-time
  `--worker-nonce`; never pass one yourself. The host refuses a component
  round without a nonce it issued, so run `make_round` as its own plain Bash
  command, never in the same command as a file edit, a heredoc or any other
  step. The hook refuses a command that names `make_round` with a call it
  cannot see (a heredoc, or no call it can parse, beyond reading the script
  with `sed`, `grep` or `cat`), and in a guarded run make_round itself
  refuses a component round without a nonce (issue #113).
- A round can take minutes. Start `make_round` with `yield_time_ms: 300000`
  and, while it runs, continue it with an empty `write_stdin` poll at
  `yield_time_ms: 300000`, and continue a yielded `exec` cell with
  `wait` at the same large yield. The poll returns as soon as the round exits,
  so the long yield never costs waiting the round did not need. Do not copy the `1000` from the `exec` pragma example
  into a poll: it is an output budget there, and as a yield it is worse than
  the 10000 ms default. Omit `yield_time_ms` before writing a small one. Never
  put a `sleep` between polls: each poll re-sends the whole session.
  On Claude Code, run `make_round` in the foreground with `Bash`
  `timeout: 600000`; it returns as soon as the round exits. A round started
  with `run_in_background` writes its exit status
  (`... > "$TMPDIR/round.log" 2>&1; echo $? > "$TMPDIR/round.exit"`) and is
  waited for with one `"$WORKSHOP_PYTHON"
  .agents/skills/autonomous-workshop/scripts/wait_for.py --exit-file
  "$TMPDIR/round.exit" --log "$TMPDIR/round.log"` call, which returns as soon
  as the round ends; never a fixed `sleep`.
- Do not read the cad scripts to learn their flags. The
  exact invocations are below; they are the same programs the host gates
  run, unchanged.
- Open `visual/sheet.png` at most once per round; the reader is the Component
  Reviewer for a component round and the Manager for an assembly round. It is one labelled image holding every
  view the round rendered -- `iso`, `front`, `left` (the side profile), `top`,
  and the tilted three-quarter views `iso_front`, `iso_back`, `iso_left`,
  `iso_right` and `iso_bottom`. The single views sit beside it at full size;
  open one only when a detail is too small to judge on the sheet. Judge the
  direction of a limb, head or weapon, and whether a form is really sculpted
  or only a round section, on the tilted view that faces it: a dead-on view
  flattens depth along its own axis. Compare against the Wish, concept,
  dimensions and reference images when present. Look for misplaced, missing or extra parts,
  size/proportion mismatch, visible intersections, wrong orientation, floating
  geometry and incorrect form. Use a targeted additional view if a part is hidden; record
  unresolved visibility as inconclusive rather than claiming a pass.
- For every reference the packet also holds `compare-NN.png`: the reference
  beside the model rendered at the reference's declared camera (`@AZ,EL`, or
  the front view when none is declared), both at one height. Under a schema 3
  Design Contract (ADR 0083) every sealed reference has its Reference Camera
  in the contract, and a component round renders the comparison from the
  Component in its Display Pose, `assembly_pose(shape, None)` (the first
  instance when the geometry's count is above 1), at that camera, under
  `visual/display-pose/`; `front`, `top` and `iso` stay in the print stance.
  A schema 3 component round of a file with no `assembly_pose` is refused
  before anything is built. A camera the host amended (`CONTRACT-AMENDMENTS.json`
  beside `WISH.json`) replaces the sealed one, and the summary's `camera`
  line says so. Judge form
  there. Look for bodies thinner or blockier than the reference, openings or
  gaps it shows that the model fills, members merged or missing, and detail
  simplified away. No silhouette score is computed anywhere in the Make
  loop (ADR 0076).
- `make_round` never lowers a threshold, never edits source, and never
  replaces the final `verify_project` run the Make gate requires. It writes
  round reports under `<project>/measure/rounds/`, component histories under
  `<project>/measure/component-rounds/<role>/`, and the reusable state at
  `<project>/measure/make-round-state.json`.
  CAD tools may update generated caches.
- Spark uses two levels. Pass one isolated round history for every component,
  then begin assembled-object rounds. Component feedback cannot stand in for
  assembly feedback, and an assembly repair that changes component geometry
  needs a recorded `--record-unlock` and invalidates that component's prior
  pass unless its rerun rebuilds the reviewed B-rep.

## Usage

```sh
"$WORKSHOP_PYTHON" .agents/skills/make-round/scripts/make_round <project>/cad \
    --ref hero=<project>/cad/ref/hero.png@-60,20 [--ref side=...@0,0] \
    [--nozzle 0.4] [--overhang-angle 45] \
    [--all-parts] [--check-motion true|false] [--json]
```

For a Spark component, select its own generator. This builds and renders only
that component, keeps its evidence under
`measure/component-rounds/<role>/`, skips project-level motion, and does not
implicitly apply whole-object reference images:

```sh
"$WORKSHOP_PYTHON" .agents/skills/make-round/scripts/make_round <project>/cad \
    --component part_<role>.step.py [--ref detail=<component-reference.png>]
```

Once every component has a first build, and before any component loop,
preview the whole object once:

```sh
"$WORKSHOP_PYTHON" .agents/skills/make-round/scripts/make_round <project>/cad \
    --preview-assembly [--entry <name>.step.py]
```

It renders the combined entry's review sheet under
`measure/assembly-previews/pNNNN/` and nothing else: no gate, no likeness, no
round history, no state, and never a pass. Use it to fix proportion, scale and
placement between parts while they are rough. Preview again only after a
component's size or placement changes.

After every component passes, start the assembled-object loop with:

```sh
"$WORKSHOP_PYTHON" .agents/skills/make-round/scripts/make_round <project>/cad \
    --require-component-passes [--ref hero=<whole-object-reference.png>]
```

That assembly command freshly builds each component and refuses to render the
assembly when any latest isolated round failed, is missing, or describes older
component geometry.

- `<project>/cad` is the directory holding the generator sources: exactly one
  entry `<name>.step.py` and any number of `part_<role>.step.py`.
- `--ref LABEL=PATH@AZ,EL` repeats once per reference view. The suffix is
  the camera the image was taken from (degrees; front `-90,0`, right `0,0`,
  iso `-45,35`); the model is rendered at that camera beside the reference.
  Without a suffix the model is shown from the front. A trailing `,TOL` is
  accepted and ignored. Omitted, the labels are read from the project's `*_spec.md`: a
  `LABEL=ref/<file>@AZ,EL` line or a row of the build spec's Likeness handoff
  table, whose camera column supplies the camera.
- Every reference the Wish sealed under `wish-references/` is shown in the
  assembly round without being named anywhere (ADR 0072). It is labelled by
  its file stem, for example `ref-01-hero`, or in Contract Mode by the
  contract's `shows` label. The exception is a sealed reference that a
  current, passing component round already showed its reviewer. In Contract
  Mode a component round shows its own `geometry:<id>` image automatically;
  outside it, pass `--ref LABEL=wish-references/<file>` to that Component's
  round. A `geometry:<id>` image with no current passing component round fails
  the assembly round; the assembly never shows it against the whole object.
  A reference that is missing or has changed fails the round. The ledger only
  needs to list references you found yourself.
- The Wish seals a reference's pixels, not the camera it was taken from. To
  give a sealed reference its camera, pass a `--ref` (or ledger entry) that
  points at that file, or a byte-identical copy of it, with the camera
  suffix: the sealed image is still shown once, under its sealed label, now
  from that camera.
- `--nozzle` is the diameter the print will use and sets the minimum wall;
  `--overhang-angle` is the slope from vertical the printer bridges unsupported.
- Only parts whose written STEP bytes changed since the previous round are
  reported; `--all-parts` reports every part. The first round reports all.
- Every part that builds is gated from source by `check_thickness` and
  `check_overhang`, which tessellate the entry in the gate and write no mesh.
  A part that did not build is reported as a gate failure, not a skip: there is
  no solid to measure. A round passes only when both gates pass on every part,
  so `built` and `printable at this nozzle` stay separate verdicts.
- A round's builds all run at once (issue #101): `gen --write`, the
  reproduction build and `brepbundle.py build`, which builds the part once
  as a gate would and keeps it as a native B-rep bundle in cadgen's derived
  cache (`__cadgen__/round-brep/`, never sealed; the latest round only), plus
  one build per instance a check places. When that build is the identity
  `gen` reported, the print gates, every Keep-out Envelope check and both
  renders read it, all at the same time, instead of building again.
  `summary.json`'s `brep` records the identity every check read: the
  bundle's read-back identity, which can differ from the build's `identity`
  by a renormalized direction (at most 1e-9 mm, recorded as `max_drift_mm`);
  the build's identity stays the round's. A check whose entry defines
  `gen_print_union()` still builds from source. `MAKE_ROUND_JOBS=1` runs the
  checks one after another.
- Each failing region names its feature: the print-details feature it lies
  on with the line that made it (`band@part_wing.step.py:42`), else the
  nearest B-rep face (`plane@(12,-4,30)`), and how far it is past the limit.
  The `wall` and `over` lines list them after `at`; the gate reports under
  the round have the rest. Repair that feature, not a coordinate.
- A feature that failed the same part's previous round too is a **Repeated
  Print Defect**: an `again` line names it and `summary.json` lists it under
  `repeated_print_defects`. Read the report's feature row before you change
  numbers again; a repeat means the last repair guessed.
- A part whose print-details features refused a size or a spot did not
  build: its **Detail Refusals** come all at once, each on a `refuse` line
  under the part's `build` line with its feature, the line that asked for
  it, the reason and what passes there, and in `summary.json` under the
  part's `build.detail_refusals`. A detail refused at the same line in the
  part's previous round too gets an `again REFUSE` line and is listed under
  `repeated_detail_refusals`, apart from `repeated_print_defects`: leave
  that detail out and name it.
- Every build runs its OCCT Booleans serially (issue #102), so one source
  gives one B-rep identity and one set of Detail Refusals; a Component file
  needs no wrapper of its own for that. A component round also builds its
  source a second time in its own process (`reproduce_build`, logged as
  `reproduce-<role>.log`). When the two builds differ in identity, or only
  one of them refuses a detail, the part did not build: its `build` line
  reads `not reproducible` with both identities (`build.identities`,
  `build.reproducible: false`). Find what the build reads besides its
  source -- an unseeded random, set or dict order, the clock, a file -- and
  rerun.
- A part whose tessellation is open is not measured. An invalid B-rep fails
  with its bad faces listed. A valid one is re-tessellated once, finer; if it
  stays open the gate's verdict is `UNMEASURABLE`, which is not a print
  failure and is never a pass: simplify the faces the report names and rerun.
- An unchanged part reuses its previous PASS only when both gates passed, the
  tool logs still hash to what was recorded, and the nozzle, angle, gate bytes
  and interpreter are identical. A failed or legacy record is always
  re-measured.
- Without `part_<role>.step.py` files, the single entry is built and reported
  as the one-piece product.
- `summary.json` records `changed` (parts whose STEP bytes moved), `checked`
  (parts with a fresh build verdict, including build failures), `print` (the
  per-part wall and overhang verdicts with their measurements) and `reused`
  (parts whose gate evidence was carried forward).
- The initial command returns exit 1 with visual status `pending` until the
  review (component) or native feedback (assembly) is recorded, even if all
  numeric checks pass. A renderer failure produces visual status `error`;
  never fabricate a review or feedback for missing images.
- Exit 0 means numeric checks and the recorded (or carried) review or visual
  feedback pass; 1 means failed, inconclusive or pending; 2 means invalid
  input, a refused review, a round the round policy refused, or the round
  could not run.

## Review a component round

A component passes when it builds, its print gates pass and an independent
reviewer agrees that it looks like its reference (ADR 0076). The Workshop
Manager does not judge its own component: each Component has one reviewer
that did not author it, spawned once and asked again in the same thread for
every later round. The request is fixed: the round's `visual-packet.json`
path and its packet sha256, nothing else, once per packet. Under a schema 4
Design Contract (ADR 0084) the round writes the Component's contract into
the packet itself, bound by the packet hash: `contract` holds its geometry
row, its `requirements` rows and the `text` of every Interface that names it
(`<id>` or `<id>#<n>`). The summary's `contract` holds the same for the
worker. Before schema 4 the packet has no `contract`, and the request also
carries that geometry's contract lines. Write its answer unchanged with the
exact packet hash from the summary:

```json
{"round": 3, "packet_sha256": "<visual packet hash from summary>",
 "reviewer": "<the reviewer's native agent id>", "agrees": false,
 "matches_plan": true, "matches_reference": false,
 "reason": "The arm reads half as thick as the reference.",
 "differences": [{"feature": "upper arm", "reference": "as thick as the leg",
                  "model": "half the leg's thickness"}]}
```

`matches_plan` and `matches_reference` are the reviewer's two separate
judgements of `sheet.png` and the comparisons (ADR 0087): against the
Component's contract rows or plan, and against its reference images,
`null` when the packet has no `compare-NN.png`. An agreeing review needs
`matches_plan` true and `matches_reference` not false.
`differences` (at most 12) is required when `agrees` is false and is the
repair list for the next round. A review may also list
`reference_conflicts` (at most 12), each `{"file", "reference",
"contract"}`: the reference image this round compared, what it shows, and
what the Design Contract requires instead, quoting the row or Interface
text. A Reference Conflict is not a difference: the Design Contract wins, it
costs no shape round, it may stand beside `"agrees": true`, and the worker
never sees it (`review.json` is written without it; the round keeps it in
`reference-conflicts.json` and the summary's `reference_conflicts`). The
final verifier reports each one, and the run reports it when it ends.
A review may also list `ruling_disputes` (at most 12), each `{"report",
"reason"}`: a ruling in the packet's `rulings` (below, Blocked Reports) the
reviewer thinks wrong. A Ruling Dispute is not a difference either: the
ruling stands, it costs no shape round, it may stand beside `"agrees":
true`, and the worker never sees it (the round keeps it in
`ruling-disputes.json` and the summary's `ruling_disputes`, and a carried
review carries it). Then record it without rebuilding:

```sh
"$WORKSHOP_PYTHON" .agents/skills/make-round/scripts/make_round <project>/cad \
    --component part_<role>.step.py --record-review <review.json>
```

It refuses a review of a round that is not the latest, a different packet
hash, changed sources, packet, renders, references or comparisons, a round
whose build or print checks failed or that has no packet, a second review of
the same round (a carried review counts), a reviewer named as the
Workshop Manager, a missing or malformed `matches_plan` or
`matches_reference`, an agreeing review whose verdicts say it misses, a malformed Reference Conflict or one naming a reference
the round did not compare, a malformed Ruling Dispute or one naming no
ruling of the packet, and a disagreeing review whose only findings are
Reference Conflicts or Ruling Disputes (such a review agrees). Where the Workshop host names the runtime
(`WORKSHOP_REVIEWER_RUNTIME`, set on Claude Code), `reviewer` must be the
reviewer's native agent id in that runtime's format (17 lowercase hex
characters), the Component's first review binds it in the component state as
`reviewer_id`, and a review naming another id is refused with the bound one.
`make_round` cannot prove who the reviewer was; the host does, at Make
acceptance, from the guard's record of which agent the runtime started and
which packet images it read. The Manager must not write, edit or filter the
review, and tells the worker only which round was reviewed: the worker reads
`review.json` in that round.

Under a schema 3 Design Contract the reviewer may answer camera mismatch
instead: the side of the model that faces the Reference Camera is not the
side the reference shows. It names the reference and the landmarks each side
shows, and replaces `agrees`, `differences`, `reference_conflicts` and
`ruling_disputes`:

```json
{"round": 3, "packet_sha256": "<visual packet hash from summary>",
 "reviewer": "<the reviewer's native agent id>",
 "reason": "The reference shows the halo face-on; the model shows its rim.",
 "camera_mismatch": {"file": "ref-03-gear-staff.png",
                     "reference": "the halo's face and its eight spokes",
                     "model": "the halo edge-on, one thin bar"}}
```

`--record-review` refuses one without landmarks, naming a reference the round
did not compare, or on a round compared without a Reference Camera. It is not
a Component Review: the Component stays awaiting review, no shape round is
spent, nothing is written to `review.json` (the claim is kept in
`camera-mismatch.json`), and the summary's `camera_mismatch.need` is the
need the Workshop Manager stops the run with. The host answers it with a
camera-only amendment; a rerun of the unchanged B-rep then shows the new
view and is reviewed afresh.

### The round policy (ADR 0081)

`make_round` makes the build -> review -> repair loop mandatory. Read the
summary's `shape` and `lock` lines, or `shape_round`, `shape_rounds_used`,
`locked` and `unlock` in `summary.json`, before deciding what to do next.
A component round prints its B-rep identity on an `identity` line and its
packet sha256 and path on a `packet` line, recorded as `identity`,
`visual.packet_sha256` and `visual.packet` in `summary.json` (issue #98):
the values a Component Worker reports.

- A round that passes build and print must be reviewed before the
  Component's geometry may change. Until its review is recorded, a round
  whose B-rep identity differs exits 2 and leaves nothing behind (the STEP it
  overwrote is put back); a rerun that leaves the geometry unchanged may run
  at any time, for example to regenerate a stale packet. Report the passing
  round and wait.
- A **shape round** is the first geometry-changing round after a disagreeing
  review. Build and print repairs, unchanged reruns, and changes forced from
  outside the Component (a Shared Helper change, an assembly unlock) are
  never shape rounds. The summary says whether this round was one and how
  many of the five are used.
- An agreeing review **locks** the Component. So does a disagreeing review
  recorded once the five shape rounds are used: it becomes a **component
  acceptance** that the run reports when it ends, so the loop cannot run on
  without end. A locked Component refuses a geometry change until something
  outside it requires one:
  - a Shared Helper the Component imports changes (detected automatically);
  - a Coupled Interface check fails and the contract names this Component
    as its yielding one (`--interface`, below; recorded automatically);
  - the Workshop Manager records that an assembly round needs it changed:

    ```sh
    "$WORKSHOP_PYTHON" .agents/skills/make-round/scripts/make_round <project>/cad \
        --component part_<role>.step.py --record-unlock <unlock.json>
    ```

    with `{"assembly_round": 4, "finding": 0, "reason": "..."}`, citing one
    finding recorded on that assembly round with `--record-visual`. It
    builds nothing.

  Rounds after an unlock are admitted and never counted. When the next
  passing round rebuilds the reviewed B-rep, with the same references and
  contract rows, the review or acceptance carries forward
  (`review.carried_from`), the round exits 0 and the Component locks again
  with no new review. A different B-rep returns it to "passed, awaiting
  review" with its shape-round count kept; a disagreeing review then, at the
  cap, is a new component acceptance.
- A component round that fails its checks is not rendered (visual status
  `not-rendered`); only a passing round is shown to the reviewer.
- A component packet binds the Component's Geometry Sources (its own source
  and the Shared Helpers it imports, directly or through another project
  module: `imported_helpers` in the summary) and its STEP. Editing any other
  file does not stale it. Every shape check reads this one definition,
  `.agents/skills/cad/scripts/geometry_sources.py` (issue #110): the assembly
  packet, an interface check, the motion evidence and `verify_project`'s
  sweep reuse go stale when a Geometry Source changes, never for a
  measurement, audit, note, sample or render.

### Interfaces between Components (ADR 0082)

When the sealed Design Contract has an `interfaces` section, three more
rules apply. Contracts without it keep the rules above unchanged.

- **Freeze the Shared Helpers first.** The Workshop Manager builds samples
  under `<project>/samples/<name>.step.py` (a peg in its socket, a pinion on
  its sector), each importing the Shared Helpers from the project, and runs:

  ```sh
  "$WORKSHOP_PYTHON" .agents/skills/make-round/scripts/make_round <project>/cad --shared-helpers
  ```

  It first checks the Shared Helper rules on every helper a Component or
  sample imports, and builds nothing while one fails (exit 1, every failure
  on stderr): each design value, a module-level UPPER_CASE name bound to a
  number or a tuple of numbers, cites `# wiki: <slug>[#section]` on its line
  or in the comment lines directly above, the page exists in the run's wiki,
  and the value appears in an `assert` of the module. A value derived from
  cited values needs no citation. A function or class named for a standard
  element (gear, pinion, rack, bearing, screw, bolt, nut, washer, thread...)
  needs `bd_warehouse` or `py_gearworks`, and no helper names an involute.
  `features/print_details.py` is exempt only while its bytes are the
  print-details library's; an edited copy is refused. Then it builds every
  sample and runs `check_thickness` and `check_overhang` on it. A pass writes `measure/shared-helpers-freeze.json` with the sha256 of
  every Shared Helper (each project `.py` module that is not an entry, a
  sample or evidence) and appends the event to
  `measure/shared-helper-freezes.jsonl`; a failing sample, or one that
  imports no Shared Helper, freezes nothing. A component round before the
  freeze exits 2. After it, a component round's `frozen` line (`helper_freeze`
  in `summary.json`) names each Shared Helper it imports that changed since
  the freeze and every Component that imports it. Rerun the check to
  re-freeze; the change is recorded as an event.
- **Keep-out Envelopes.** For each separable Interface a Component joins, its
  round runs `check_envelope` on its B-rep: the inside Component, placed by
  its entry's `assembly_pose(shape, pose)` at every declared pose, stays
  inside that pose's shape; the outside Component, placed with `pose` None,
  stays out of every shape. A failure fails the round's checks like a print
  gate (the `keep` line, `envelopes` in `summary.json`).
- **Instances (issue #80).** An Interface may name one instance of a Unique
  Geometry whose count is above 1, `<id>#<n>` (`wing#1`, `wing#2`). The
  geometry's one `part_<id>.step.py` builds and places every instance:
  `assembly_pose(shape, pose, instance)` places instance n, and
  `gen_step(instance=1)` builds it when the instances differ (a `gen_step`
  without `instance` builds identical copies). A file whose `assembly_pose`
  takes no `instance` fails the envelope check and is refused by
  `--interface`, with a message naming this convention. An envelope side
  that is an instance runs `check_envelope --instance n`, reported as
  `<interface> <id>#<n>`; instances on both sides run both checks in the
  same round.
- **Coupled Interfaces.** Once every Component an Interface joins is locked:

  ```sh
  "$WORKSHOP_PYTHON" .agents/skills/make-round/scripts/make_round <project>/cad --interface <id>
  ```

  It refuses (exit 2) a separable or static Interface and any Component not
  locked at its current geometry, builds those Components only, places them
  through `assembly_pose(shape, None)` and runs `check_motion`'s
  `coupled_motion_collision` over the sealed pose table (or the
  `measure/motion.json` condition its `poses_from` names), with the
  non-moving Components as obstacles. Each instance an Interface names is
  its own child, labelled `<id>#<n>`, which the pose table's movers name;
  locking, staleness and the unlock belong to its Component, built once, so
  a failure yielding `wing#2` unlocks the wing. Rounds live under
  `measure/interface-rounds/<id>/`. A failure unlocks the yielding
  Component with the check's evidence; its repair is never a shape round.
  A check stays current until a Component it joins changes identity or one
  of their Geometry Sources changes (`sources` in its state).
  `--require-component-passes` refuses assembly while any Coupled Interface
  lacks a current passing check, and so does the final verifier, which lists
  every Interface with its proof in `component-acceptance.json`.

### Blocked Reports (issue #88)

A Component Worker that cannot proceed -- two of its contract rows cannot
both hold, a stated print rule (stance, "no part needs support") its
geometry cannot meet, or a choice only the Workshop Manager may make --
records a Blocked Report, then reports blocked:

```bash
"$WORKSHOP_PYTHON" .agents/skills/make-round/scripts/make_round <project> \
    --component part_<role>.step.py --report-blocked <blocked.json>
```

`blocked.json` is `{"rows": [...], "reason": "..."}`, each row copied
verbatim from the sealed Design Contract (whitespace aside); a row that is
not in it is refused, and so is a second report while one of the
Component's reports is open. The report records the Component, its latest
round and the rows in `measure/blocked-reports.jsonl`, bound to the run by
the sha256 of `WISH.json`. It builds nothing and takes no nonce.

The Workshop Manager answers it with `--clear-blocked <answer.json>`:

- `{"report": N, "decision": "..."}`: a ruling inside a freedom the
  contract grants; the worker follows it with a new round or a new report.
- `{"report": N, "decision": "...", "waits_on": "part_<other>.step.py"}`:
  the report stays open, waiting, until that Component's next round whose
  checks pass. That round's summary carries `wakes_blocked` and a `wake`
  line, and `--blocked-reports` shows the report `WOKEN`; the Manager then
  clears it with a new decision for the worker.
- `{"report": N, "need": "..."}`: a Contract Contradiction, one line that
  quotes every row; the Manager seals it with `stage_proposal.py need`.
- `{"report": N, "amendment": M}`: Contract Amendment M, which names report
  N, was applied (below).

`--blocked-reports [--json]` lists every report and its answers, and exits
1 while one is open, waiting or woken. While any is open or waiting an
assembly round and `--full` refuse to run; the Make finalizer and the host
refuse the Make proposal and Make acceptance, and on Claude Code a hook
refuses the root's turn end unless it ends on a recorded need. The tool is
the same on every runtime; no hook is needed to report or clear.

A decided ruling binds the Component Reviewer (issue #97). Every later
component round of that Component writes its decided rulings, oldest first,
into the visual packet and the summary as `rulings`: `{"report", "round",
"rows", "request", "ruling", "decided_at"}`, copied from the ledger (the
worker's report as `request`, the Manager's last decision as `ruling`). Only
a report whose last answer is a decision that waits on nothing is a ruling.
The rulings join the carry key, so a review carries to a later round only
under the same rulings; without any, packet and key are unchanged. An
unchanged rerun after a new ruling is therefore reviewed afresh and is not
a shape round. `--record-review` refuses a review of a packet rendered
before the Component's latest ruling; the worker reruns unchanged. An
unreadable ledger refuses the component round before anything is built.

### Contract Amendments (ADR 0085)

When a Contract Contradiction's smallest fix changes nothing a sealed
reference image shows, the Workshop Manager may amend the rows inside the
run instead of stopping on a need:

```bash
"$WORKSHOP_PYTHON" .agents/skills/make-round/scripts/make_round <project> \
    --propose-amendment <proposal.json>
```

`proposal.json` is `{"rows": [...], "changes": [{"from": "...", "to":
"..."}], "reason": "...", "report": N}`: two or more contract statements
that cannot both hold, verbatim; each change replaces one whole requirement
text or (schema 4) Interface text, and nothing else; `report` is optional.
The tool writes `measure/contract-amendments/aNN/packet.json` (the rows, the
changes, the reason and every sealed reference by path and sha256),
appends the proposal to `measure/contract-amendments.jsonl` bound to the
sha256 of `WISH.json` and to the canonical-JSON hash of the contract it
amends, and prints the packet path and hash. A fresh `contract-reviewer`
reads the packet and every reference and answers `contradiction`,
`smallest`, `visible_in` and `references_checked`; the Manager records it
with `--record-amendment-review <review.json>`, adding `amendment`,
`packet_sha256` and `reviewer`. It applies only when both are true and
`visible_in` is empty, and exits 1 otherwise with the need to stop on. A
reviewer is refused when it is the Manager, a Component's reviewer, or the
reviewer of an earlier amendment.

A refusal with `contradiction` true, `visible_in` empty and `smallest`
false allows one Smaller Retry (issue #96): a new proposal with the same
rows whose every change is a row the refused amendment changed, from the
same text, with only deletions applied (shorter, a subsequence, no word
added or respelled). The proposal and its packet record `retry_of`, and
`--record-amendment-review` prints the reviewer's reason after a refusal
that allows it. Any other proposal quoting rows an earlier amendment quoted
is refused: a third one, one after a contradiction or visibility refusal,
or one after an applied amendment.

After an amendment applies, every round reads the sealed contract with the
amended rows: the rows a component round delivers, the rows a Blocked Report
quotes, and the contract-rows hash its review binds. A locked Component
whose rows changed unlocks (summary `unlock a Contract Amendment changed
this Component's rows`), and no earlier review carries across the change.
One amendment awaits review at a time; while it does, an assembly round and
`--full` refuse to run and the finalizer refuses the Make proposal.
`--contract-amendments [--json]` lists every amendment and exits 1 while
one awaits review. The host replays the ledger against the sealed contract
before it accepts Make.

The owner may also amend the contract on resume (`workshop resume
--amend-contract`, issue #100). The host appends an Owner Contract
Amendment (`owner_amendments`: each changed row before and after, the
Components whose own rows changed, the contract hash before and after) to
the run root's `CONTRACT-AMENDMENTS.json`, and for a run whose objective is
its contract also writes the amended `objective`. Rounds read the owner's
rows after every applied in-run amendment, so a locked Component whose own
rows changed unlocks as above; an owner's assembly row binds no Component.
`--contract-amendments` lists each owner amendment after the in-run ones,
and from then on `--propose-amendment` is refused. The host refuses an
owner amendment for a run whose `make_round` or finalizer lacks the marker
`workshop-owner-contract-amendments-v1`.

## Record assembly visual feedback

The native Manager performs the assembly's visual judgment. Python renders and hashes
evidence; it never calls a vision model, diagnoses an image or chooses repairs.
A clean build and green gates are not a form verdict. Open `sheet.png` and
judge in this order:

1. **Silhouette, stance and shape language.** Does the outline read as the
   intended object in the intended pose from every view, and do its sections,
   edges, points and proportion carry the style the plan states (for example
   angular, creased and gaunt rather than round, filleted and full)?
2. **Proportion between parts.** Head to body, limb length and thickness,
   against the plan and, when a `## Reference reading` exists, its measured
   `[observed]` ratios.
3. **Surface detail at render scale.** Does relief, texture or ornament
   actually read, or is it too shallow to see?

Judge twice, separately: against the plan the object is built from
(`WISH-EXPANSION.md`, the sealed concept, or the Design Contract) as
`matches_plan`, and against the round's reference images as
`matches_reference` -- `null` when the round has none. Name a defect whenever
the render falls short. The common ones: round or boxy massing where the form
should be sculpted (a loft of circles or ellipses is still a tube), a shape
language the plan did not ask for (soft and inflated where it asked for hard
and angular), a
silhouette that reads as a different object, relief too shallow to see, a part
that lost its shape. Reporting a real defect is the intended outcome, not a
failure: the round hands the attempt back so it can be fixed.

When the silhouette or massing is wrong, the repair is usually a different
construction family (loft with shaped sections, sweep, revolve, sketch
profile), not smaller parameter nudges on a shape that reads incorrectly:
those rarely converge.

After inspecting the packet, write this JSON with the exact packet hash from
the summary. Each defect names the affected part, visible error, view/location
evidence, and proposed source correction. Keep observations short and concrete.

```json
{
  "packet_sha256": "<visual packet hash from summary>",
  "status": "fail",
  "matches_plan": false,
  "matches_reference": null,
  "observation": "The body is coherent, but the left wheel is visibly offset.",
  "findings": [{
    "part": "left wheel",
    "defect": "Axle is above the wheel centre",
    "evidence": "Front view: axle meets the upper third of the wheel",
    "repair": "Align the wheel centre with the axle datum in the source"
  }]
}
```

`pass` is refused unless `matches_plan` is true and `matches_reference` is not
false, and `matches_reference` must be a boolean exactly when the round has
reference images. Use `pass` with an empty findings list only after inspection
finds no errors;
use `inconclusive` and describe the missing evidence when a verdict is impossible.

Add `differences` for every way the model's form differs from a reference in
`compare-NN.png`, at most 12.

```json
"differences": [{
  "feature": "claws",
  "reference": "three hooked claws reaching 37 mm",
  "model": "three straight claws stopping at 18 mm",
  "decision": "keep",
  "reason": "The Design Contract fixes 18 mm claws (R23)"
}]
```

`decision` is `repair` or `keep`. A difference to `repair` cannot pass; it
needs a matching finding and a new round. A kept difference names what forces
it. An observation that repeats the previous round's is refused: inspect each
round's images afresh (ADR 0075).
Then run:

```sh
"$WORKSHOP_PYTHON" .agents/skills/make-round/scripts/make_round <project>/cad \
    --record-visual <feedback.json>
```

This updates the same round's summary with detected visual errors. It rejects
changed source/constraint bytes, changed renders/references/comparisons, wrong
packet hashes, contradictory findings, a copied observation and repeat
submissions. A component round does not take `--record-visual`. Source edits start a new round;
never rebind prior prose to new hashes. Manager self-review does not consume or
replace the independent blind critic allowance.

## Final review

Final Make allows an initial independent blind review plus up to three focused
repair-and-rereview cycles (four reviews total). After a passing hash-bound
blind review, the final `--record-visual` may also use
`--full` to invoke `verify_project --strict-fit` once. Normally run
the integrated verifier directly after blind review; never start a new round
just to run it. The host alone performs the authoritative `--fresh` rebuild.

## Summary

The summary names, in order: the changed parts with their build and print
verdicts, any reference that could not be shown, which round each sealed
reference was shown to, a component's shape-round count, the motion gate
verdict, the visual findings and differences, the component review and any
acceptance at the shape-repair limit, and the `--full` verdict when requested. Everything the tools printed is kept
under `measure/rounds/rNNNN/` beside `summary.json`.

## Tool card

Every gate `make_round` runs, exactly as it runs it. `$C` is
`.agents/skills/cad/scripts`.

| Step | Invocation | Reads |
|---|---|---|
| build a part | `"$WORKSHOP_PYTHON" $C/gen part_<role>.step.py --write --json` | exit code, and the sibling `part_<role>.step` it writes |
| build a sample | `PYTHONPATH=<project> "$WORKSHOP_PYTHON" $C/gen samples/<name>.step.py --write --json`, then both print gates | exit codes and gate verdicts |
| keep-out envelope | `"$WORKSHOP_PYTHON" .agents/skills/make-round/scripts/check_envelope part_<role>.step.py --envelope <round>/envelope-<id>.json --role inside\|outside --json` | `ok` and the per-pose volumes outside or inside the envelope |
| interface check | `"$WORKSHOP_PYTHON" $C/check_motion <project> --manifest measure/interface-rounds/<id>/rNNNN/motion.json --json` | the one `coupled_motion_collision` condition's `status` |
| motion | `"$WORKSHOP_PYTHON" $C/check_motion <project> --manifest measure/motion.json --json` | `status` per condition: `pass`, `fail`, `inconclusive` |
| inspection views | `"$WORKSHOP_PYTHON" $C/render_review <selected entry.step.py> --view iso --view front --view left --view top --view iso_front --view iso_back --view iso_left --view iso_right --view iso_bottom [--view=AZ,EL ...] --sheet -o <round>/visual` | `sheet.png` (every view, labelled) plus each exact shaded PNG; the reference-camera views are composed into `compare-NN.png` beside each reference |
| final verify | `"$WORKSHOP_PYTHON" $C/verify_project <project> --strict-fit --print-gates [--image-derived] --report <project>/measure/verification-pipeline.md` | exit 0 = verifier passed; host gate still required |
| motion sheet | `"$WORKSHOP_PYTHON" $C/motion_presentation.py` (see the cad skill) | presentation only, not a gate |

## What this is not

It batches deterministic tools and records native judgment. Numeric verdicts
come from the original tools; visual judgments come from the reviewer's or
the Manager's actual image inspection. It cannot independently verify the truth of those findings.
The thresholds are the tools' defaults unless you pass them, and the
final Make proposal still requires the integrated `verify_project` run the
cad skill describes.

## Interrupted geometry analysis

A cancelled or timed-out print/motion measurement is `UNVERIFIED`, never PASS.
The round can continue to visual review with that explicit limitation;
`geometry_status: unverified` and `print_ready_claim: false` retain it in the
summary. Repair measured failures. Do not repeat a round solely to retry the
same timed-out geometry operation. Final `verify_project` seals incomplete
checks into the final geometry disclosure. An incomplete print check supplies
no passing report: use the existing empty `print_gate_sha256s` no-claim case in
signature review rather than inventing passing thickness/overhang evidence.
If a build itself fails, repair it: an inspection waiver cannot create missing
STEP assets. All child commands run in an owned, cancellable process group.
