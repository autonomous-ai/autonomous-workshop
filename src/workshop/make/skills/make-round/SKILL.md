---
name: make-round
description: Run one Make iteration as a single command — export the parts, wall-check what changed, score likeness against the Wish references, run the motion gate, and read one short summary — instead of a dozen separate tool calls and a dozen source reads. Use for every Make repair round of a CAD product; not a replacement for the final integrated verify_project, which it can also invoke once with --full.
---

# Make round

One Make iteration, one command, one summary. This skill exists because a
Make session's cost is the number of model requests times the context each
carries: the first published wind-up microduck (2026-09-07) spent 673 shell
calls and 925 model requests, and 430 of those shell calls were `cat`, `rg`,
`sed`, and `tail` over skill sources and the run's own logs. This page is the
tool card those reads were looking for, and `make_round` is the loop those
calls were reassembling by hand.

## Rules

- Run `make_round` once per repair round, after editing source and before
  deciding what to repair next. Read its summary; open a full report only
  when the summary names a failure you cannot place.
- Do not read the cad or image-to-cad scripts to learn their flags. The
  exact invocations are below; they are the same programs the host gates
  run, unchanged.
- View an image at most once per round, and only when a decision depends on
  something a number cannot tell you. Every image you view stays in the
  session context for every later request. The likeness score, the motion
  gate, and the thickness regions are numbers; use them first.
- `make_round` never lowers a threshold, never edits source, and never
  replaces the final `verify_project` run the Make gate requires. It writes
  under `<project>/measure/rounds/` and touches nothing else.

## Usage

```sh
"$WORKSHOP_PYTHON" .agents/skills/make-round/scripts/make_round <project>/cad \
    --ref hero=<project>/cad/ref/hero.png [--ref side=...] \
    [--min 0.90] [--nozzle 0.4] [--all-parts] [--no-motion] [--full] [--json]
```

- `<project>/cad` is the directory holding the generator sources: exactly one
  entry `<name>.step.py` and any number of `part_<role>.step.py`.
- `--ref LABEL=PATH` repeats once per reference view. Omitted, the labels are
  read from the `LABEL=ref/<file>` lines of the project's `*_spec.md`.
- Only parts whose exported STL bytes changed since the previous round are
  wall-checked; `--all-parts` checks every part. The first round checks all.
- `--full` also runs `verify_project --fresh --exports --strict-fit`, with
  `--image-derived --likeness-ref` for each reference, after the round; use it
  once, when the round is clean and you are about to propose.
- Exit status 0 means every check it ran passed; 1 means at least one
  failed; 2 means the round could not run (no entry, a tool missing).

The summary names, in order: the parts that changed and their wall verdicts
with the thinnest region, the likeness score per view with the change since
the previous round and the pose it was scored at, the motion gate verdict,
and the `--full` verdict when requested. Everything the tools printed is kept
under `measure/rounds/rNNNN/` beside `summary.json`.

## Tool card

Every gate `make_round` runs, exactly as it runs it. `$C` is
`.agents/skills/cad/scripts`, `$I` is `.agents/skills/image-to-cad/scripts`.

| Step | Invocation | Reads |
|---|---|---|
| export a part | `"$WORKSHOP_PYTHON" $C/export part_<role>.step.py --stl <out>.stl --json` | `files[].path` |
| wall check | `"$WORKSHOP_PYTHON" $C/check_thickness <stl> --nozzle 0.4 --report <md>` | `PASS`/`FAIL` lines, `RESULT:` line, exit 1 on a thin wall |
| likeness | `"$WORKSHOP_PYTHON" $I/render_views.py <entry>.step.py --match <ref.png> --label <L> --min 0.90 -o <dir> --shaded --json [--poses-from <prev poses.json>]` | `results[].iou`, `.ok`, `.az/.el/.roll/.fov` |
| motion | `"$WORKSHOP_PYTHON" $C/check_motion <project> --manifest measure/motion.json --json` | `status` per condition: `pass`, `fail`, `inconclusive` |
| final verify | `"$WORKSHOP_PYTHON" $C/verify_project <project> --fresh --exports --strict-fit [--image-derived --likeness-ref L=PATH ...] --report <md>` | exit 0 = sealed-ready; the report is the record |
| motion sheet | `"$WORKSHOP_PYTHON" $C/motion_presentation.py` (see the cad skill) | presentation only, not a gate |

`render_views.py --match` searches the camera pose and scores with the
likeness gate's own comparison; `--poses-from` replays the previous round's
pose so consecutive rounds measure the model, not the camera. A reference
with a transparent background is read from its alpha channel. When the replay scores under the floor, `make_round` re-searches a +/-30 degree window around that camera and keeps the better score, marked `(re-searched)` in the summary; a moved part is otherwise scored under a stale camera.

## What this is not

It is orchestration, not judgment. Every verdict comes from the original
tool, the thresholds are the tools' defaults unless you pass them, and the
final Make proposal still requires the integrated `verify_project` run the
cad skill describes.
