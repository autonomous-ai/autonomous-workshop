# Image-derived CAD verification

Read this file when a CAD project originates from photographs, illustrations,
or a build spec produced by `image-to-cad`.

Geometry soundness and visual fidelity are separate claims. The integrated
final workflow is:

```bash
CADGEN_WARM=1 python "$CAD_SKILL_ROOT/scripts/verify_project" <project-dir> --fresh --exports \
  --image-derived \
  --likeness-ref hero=ref/hero.png \
  --likeness-ref side=ref/side.png
```

Reference paths must remain inside the project. Give every usable viewpoint;
do not choose only the image the model happens to match best. The runner writes
the orthogonal review set and searched reference poses under `snap/`, records
the cameras in `snap/poses.json`, writes `measure/likeness.md`, and fails when
any pair is below `--likeness-min` (0.90 by default). It also runs
`render_views.py --compare-step`; a drift finding means the exported STEP is
not the geometry the source currently builds.

## The two required local audits

The runner requires these files because neither claim is generic enough for a
manifest that merely repeats the source.

### `measure/check_spec.py`

This is the source/spec reconciliation gate. It exits zero only when the
approved `*_spec.md` describes the current source. At minimum it checks:

- governing scale and overall bounding-box targets, with the spec tolerance;
- printed part count, assembly labels, and named mechanism or connector rows;
- each defining feature's current construction family (loft, sweep, revolved
  profile, shell, or other operation named by the spec), not just its presence
  as a Python identifier;
- every parameter or feature deliberately changed during CAD repair is also
  changed in the spec, or explicitly recorded as an accepted deviation.

Assertions must name the spec row and show expected versus actual values. A
script that only imports the source or searches for keywords is not an audit.

### `measure/check_landmarks.py`

This is the landmark-ledger gate. It builds or imports the current combined
assembly and gives every defining visual landmark a local target: count, bbox,
axis, station, labelled child, or measured relationship. Small details need
their own target because the global silhouette can hide their omission.

The audit must fail on an omitted ledger item. It may share project builders,
but it must measure the returned geometry rather than restating the arithmetic
that created it. Keep silhouette questions in `check_likeness.py`; keep exact
distances and alignments in `inspect measure/align/frame`.

Both scripts run with the project directory prepended to `PYTHONPATH` and the
workspace as the current directory. They take no mandatory arguments, print a
short pass/fail record, and use exit status 0 for pass, 1 for a failed claim,
and 2 for invalid audit setup.

## Repair loop

Run cheap checks and renderer views from the generator while iterating. Do not
write STEP files repeatedly merely to look at a change. After a shared library
edit, clear the project `__cadgen__/` cache before the one final multi-target
`gen --write`; then let `verify_project` compare that STEP back to the source.

If a likeness band or landmark check causes a source change, reconcile the
spec in the same edit. A final run with stale prose is a failed run even when
the source geometry improved.
