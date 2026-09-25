---
name: make-round
description: Run isolated component or assembled-object Make repair rounds with deterministic CAD checks and native visual inspection. Render the selected scope, inspect form and proportions, and record visual errors alongside likeness, build and motion results. Does not replace independent blind review or final verification.
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
computed on the shape it just built, never on an import. For a source archive
sealed before `made.json` carried this hash (every archive today -- see issue
#64), get the source side by rebuilding the source's own `part_<role>.step.py`
in a scratch copy of its `make/` tree with the same `gen --write --json` and
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
  deciding what to repair next. Then inspect the visual packet and record the
  Manager's findings using `--record-visual` without rebuilding. Read its summary; open a full report only
  when the summary names a failure you cannot place.
- A round can take minutes. Start `make_round` with `yield_time_ms: 30000` and,
  while it runs, continue it with an empty `write_stdin` poll at
  `yield_time_ms: 30000` or more, and continue a yielded `exec` cell with
  `wait` at the same large yield. The poll returns as soon as the round exits,
  so the long yield never costs waiting the round did not need. Do not copy the `1000` from the `exec` pragma example
  into a poll: it is an output budget there, and as a yield it is worse than
  the 10000 ms default. Omit `yield_time_ms` before writing a small one. Never
  put a `sleep` between polls: each poll re-sends the whole session.
- Do not read the cad or image-to-cad scripts to learn their flags. The
  exact invocations are below; they are the same programs the host gates
  run, unchanged.
- View each image at most once per round. Always inspect the front, top and iso
  views in `visual-packet.json`, together with the Wish, concept, dimensions and
  reference images when present. Look for misplaced, missing or extra parts,
  size/proportion mismatch, visible intersections, wrong orientation, floating
  geometry and incorrect form. A high likeness score cannot establish visual
  correctness. Use a targeted additional view if a part is hidden; record
  unresolved visibility as inconclusive rather than claiming a pass.
- `make_round` never lowers a threshold, never edits source, and never
  replaces the final `verify_project` run the Make gate requires. It writes
  round reports under `<project>/measure/rounds/`, component histories under
  `<project>/measure/component-rounds/<role>/`, and the reusable state at
  `<project>/measure/make-round-state.json`.
  CAD tools may update generated caches.
- Spark uses two levels. Pass one isolated round history for every component,
  then begin assembled-object rounds. Component feedback cannot stand in for
  assembly feedback, and an assembly repair that changes component geometry
  invalidates that component's prior pass.

## Usage

```sh
"$WORKSHOP_PYTHON" .agents/skills/make-round/scripts/make_round <project>/cad \
    --ref hero=<project>/cad/ref/hero.png [--ref side=...] \
    [--min 0.90] [--nozzle 0.4] [--overhang-angle 45] \
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
- `--ref LABEL=PATH` repeats once per reference view. Omitted, the labels are
  read from the project's `*_spec.md`: a `LABEL=ref/<file>` line or a row of
  the build spec's Likeness handoff table.
- Every reference the Wish sealed under `wish-references/` is scored in the
  assembly round without being named anywhere (ADR 0072). It is labelled by
  its file stem, for example `ref-01-hero`. The one exception is a sealed
  reference that a current, passing component round already scored at or
  above the floor. To use that exception for a reference that shows a single
  Component, pass `--ref LABEL=wish-references/<file>` to that Component's
  round. Otherwise the reference is scored against the whole object and
  fails there. A sealed reference that is missing or has changed fails the
  round. The ledger only needs to list references you found yourself.
- `--nozzle` is the diameter the print will use and sets the minimum wall;
  `--overhang-angle` is the slope from vertical the printer bridges unsupported.
- Only parts whose written STEP bytes changed since the previous round are
  reported; `--all-parts` reports every part. The first round reports all.
- Every part that builds is gated from source by `check_thickness` and
  `check_overhang`, which tessellate the entry in the gate and write no mesh.
  A part that did not build is reported as a gate failure, not a skip: there is
  no solid to measure. A round passes only when both gates pass on every part,
  so `built` and `printable at this nozzle` stay separate verdicts.
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
- The initial command returns exit 1 with visual status `pending` until native
  feedback is recorded, even if all numeric checks pass. A renderer failure
  produces visual status `error`; never fabricate feedback for missing images.
- Exit 0 means numeric checks and recorded visual feedback pass; 1 means failed,
  inconclusive or pending; 2 means invalid input or the round could not run.

## Record visual feedback

The native Manager performs the visual judgment. Python renders and hashes
evidence; it never calls a vision model, diagnoses an image or chooses repairs.
After inspecting the packet, write this JSON with the exact packet hash from
the summary. Each defect names the affected part, visible error, view/location
evidence, and proposed source correction. Keep observations short and concrete.

```json
{
  "packet_sha256": "<visual packet hash from summary>",
  "status": "fail",
  "observation": "The body is coherent, but the left wheel is visibly offset.",
  "findings": [{
    "part": "left wheel",
    "defect": "Axle is above the wheel centre",
    "evidence": "Front view: axle meets the upper third of the wheel",
    "repair": "Align the wheel centre with the axle datum in the source"
  }]
}
```

Use `pass` with an empty findings list only after inspection finds no errors;
use `inconclusive` and describe the missing evidence when a verdict is impossible.
Then run:

```sh
"$WORKSHOP_PYTHON" .agents/skills/make-round/scripts/make_round <project>/cad \
    [--component part_<role>.step.py] --record-visual <feedback.json>
```

This updates the same round's summary with detected visual errors. It rejects
changed source/constraint bytes, changed renders/references, wrong packet hashes,
contradictory findings and repeat submissions. Source edits start a new round;
never rebind prior prose to new hashes. Manager self-review does not consume or
replace the independent blind critic allowance.

Final Make allows an initial independent blind review plus up to three focused
repair-and-rereview cycles (four reviews total). After a passing hash-bound
blind review, the final `--record-visual` may also use
`--full` to invoke `verify_project --strict-fit` once. Normally run
the integrated verifier directly after blind review; never start a new round
just to run it. The host alone performs the authoritative `--fresh` rebuild.

The summary names, in order: the changed parts and their build verdicts, the
likeness score per view with the change since
the previous round and the pose it was scored at, the motion gate verdict,
the native visual findings, and the `--full` verdict when requested. Everything the tools printed is kept
under `measure/rounds/rNNNN/` beside `summary.json`.

## Tool card

Every gate `make_round` runs, exactly as it runs it. `$C` is
`.agents/skills/cad/scripts`, `$I` is `.agents/skills/image-to-cad/scripts`.

| Step | Invocation | Reads |
|---|---|---|
| build a part | `"$WORKSHOP_PYTHON" $C/gen part_<role>.step.py --write --json` | exit code, and the sibling `part_<role>.step` it writes |
| likeness | `"$WORKSHOP_PYTHON" $I/render_views.py <entry>.step.py --match <ref.png> --label <L> --min 0.90 -o <dir> --shaded --json [--poses-from <prev poses.json>]` | `results[].iou`, `.ok`, `.az/.el/.roll/.fov` |
| motion | `"$WORKSHOP_PYTHON" $C/check_motion <project> --manifest measure/motion.json --json` | `status` per condition: `pass`, `fail`, `inconclusive` |
| inspection views | `"$WORKSHOP_PYTHON" $C/render_review <selected entry.step.py> --view front --view top --view iso -o <round>/visual` | exact shaded PNGs for native Manager inspection of one component or the assembly |
| final verify | `"$WORKSHOP_PYTHON" $C/verify_project <project> --strict-fit [--image-derived --likeness-ref L=PATH ...] --report <project>/measure/verification-pipeline.md` | exit 0 = verifier passed; host gate still required |
| motion sheet | `"$WORKSHOP_PYTHON" $C/motion_presentation.py` (see the cad skill) | presentation only, not a gate |

`render_views.py --match` searches the camera pose and scores with the
likeness gate's own comparison; `--poses-from` replays the previous round's
pose so consecutive rounds measure the model, not the camera. Each reference
keeps its own pose file; the summary records the selected file as
`poses_path`. A bounded search writes separate evidence, and its pose is
retained only when its score is better than the replay. A reference
with a transparent background is read from its alpha channel. When the replay scores under the floor, `make_round` re-searches a +/-30 degree window around that camera and keeps the better score, marked `(re-searched)` in the summary; a moved part is otherwise scored under a stale camera.

## What this is not

It batches deterministic tools and records native judgment. Numeric verdicts
come from the original tools; visual findings come from the Manager's actual
image inspection. It cannot independently verify the truth of those findings.
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
