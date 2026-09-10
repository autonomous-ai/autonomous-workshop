---
name: make-round
description: Run each Make repair round with deterministic CAD checks and native visual inspection. Render the model, inspect placement and proportions, and record visual errors alongside likeness, build and motion results. Does not replace independent blind review or final verification.
---

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
  while it runs, continue it with `write_stdin` at the same yield. Never put a
  `sleep` between polls: each poll re-sends the whole session.
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
  round reports under `<project>/measure/rounds/` and the reusable state at
  `<project>/measure/make-round-state.json`.
  CAD tools may update generated caches.

## Usage

```sh
"$WORKSHOP_PYTHON" .agents/skills/make-round/scripts/make_round <project>/cad \
    --ref hero=<project>/cad/ref/hero.png [--ref side=...] \
    [--min 0.90] [--nozzle 0.4] [--overhang-angle 45] \
    [--all-parts] [--no-motion] [--json]
```

- `<project>/cad` is the directory holding the generator sources: exactly one
  entry `<name>.step.py` and any number of `part_<role>.step.py`.
- `--ref LABEL=PATH` repeats once per reference view. Omitted, the labels are
  read from the `LABEL=ref/<file>` lines of the project's `*_spec.md`.
- `--nozzle` is the diameter the print will use and sets the minimum wall;
  `--overhang-angle` is the slope from vertical the printer bridges unsupported.
- Only parts whose written STEP bytes changed since the previous round are
  reported; `--all-parts` reports every part. The first round reports all.
- All geometry entries are built; only the printable subset is gated from
  source by `check_thickness` and `check_overhang`, which tessellate in the gate
  and write no mesh. Mixed-material sources explicitly declare literal
  `PRINTABLE = True` for printed components and `False` for nonprinted geometry,
  including the combined entry. A build failure still fails the round. Both
  print gates must pass for every printable source; nonprinted geometry gets
  no print PASS and remains part of complete-product visual inspection.
- An unchanged part reuses its previous PASS only when both gates passed, the
  tool logs still hash to what was recorded, and source hashes, nozzle, angle,
  gate bytes and interpreter are identical. A failed or legacy record is always
  re-measured.
- Without `part_<role>.step.py` files, the single entry is built and reported
  as the one-piece product.
- `summary.json` records `changed` (parts whose STEP bytes moved), `checked`
  (parts with a fresh build verdict, including build failures), `print` (the
  printable subset's wall and overhang verdicts with their measurements) and `reused`
  (parts whose gate evidence was carried forward).
- The initial command returns exit 1 with visual status `pending` until native
  feedback is recorded, even if all numeric checks pass. A renderer failure
  produces visual status `error`; never fabricate feedback for missing images.
- Exit 0 means numeric checks and recorded visual feedback pass; 1 means failed,
  inconclusive or pending; 2 means invalid input or the round could not run.
- Final `--full` verification uses print gates only when printable sources
  exist. An all-nonprinted project records `full.print_gates_ran: false` and
  `full.print_ready_claim: false`; passing geometry does not certify its
  fabrication, assembly or physical function.

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
    --record-visual <feedback.json>
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
just to run it. The Make finalizer is still required. Spark accepts Make's
verification without a duplicate host rebuild; other workflows retain their
materialized host-verification policy.

When using this final shortcut, pass `--powered` for any functional electrical
load. An image-derived round (one with reference views) requires an explicit
choice: `--powered` or `--unpowered`. For example, after independent blind review:

```sh
"$WORKSHOP_PYTHON" .agents/skills/make-round/scripts/make_round <project>/cad \
    --record-visual <feedback.json> --full --powered
```

Use `--unpowered` instead for an image-derived product with no functional
electrical load. The flags are mutually exclusive and only valid with
`--record-visual --full`; `--unpowered` requires reference views. Missing
classification for an image-derived final run is refused before feedback is
recorded. Classification is never inferred from a missing power manifest.
The unchanged verifier requires `measure/power.json` for `--powered` and
refuses `--unpowered` if that manifest exists. It still validates the independent
review and all engineering gates. Unflagged non-image-derived runs retain their
existing behavior. The final summary records the explicit choice, or `null`
when none was supplied.

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
| inspection views | `"$WORKSHOP_PYTHON" $C/render_review <entry.step.py> --view front --view top --view iso -o <round>/visual` | exact shaded PNGs for native Manager inspection |
| final verify | `"$WORKSHOP_PYTHON" $C/verify_project <project> --strict-fit [--print-gates --nozzle N] [--powered \| --unpowered] [--image-derived --likeness-ref L=PATH ...] --report <project>/measure/verification-pipeline.md` | explicit power choice forwarded; exit 0 = verifier passed; Make finalizer still required; Spark has no duplicate host rebuild |
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
