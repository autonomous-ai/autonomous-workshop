# Image-derived CAD verification

Read this file when a CAD project originates from photographs, illustrations,
or a build spec produced by `image-to-cad`.

Geometry soundness and visual fidelity are separate claims. The integrated
final workflow is:

```bash
CADGEN_WARM=1 python "$CAD_SKILL_ROOT/scripts/verify_project" <project-dir> --fresh --print-gates \
  --image-derived --unpowered \
  --likeness-ref hero=ref/hero.png@-45,25 \
  --likeness-ref side=ref/side.png@0,0
```

Replace `--unpowered` with `--powered` whenever the approved spec declares a
functional electrical load. The mode requires one explicit classification;
`--powered` also requires `measure/power.json`.

Reference paths must remain inside the project. Give every usable viewpoint;
do not choose only the image the model happens to match best. Each reference
declares the camera it was taken from as `@AZ,EL[,TOL]` (degrees, in
`render_views.py`'s frame: front is -90,0, right is 0,0; TOL defaults to 30).
The pose search stays inside that window and checks the model's reflections
there, because a search over every azimuth scores a mirror-image model like
the right one; a `HANDEDNESS SUSPECT` failure is a source fix across the named
axis. A reference without a camera is refused. See
`skills/image-to-cad/references/likeness-gate.md`. The runner writes
the orthogonal review set and searched reference poses under `snap/`, records
the cameras in `snap/poses.json`, writes `measure/likeness.md`, and fails when
any pair is below the 0.90 delivery floor. The integrated runner never lowers
that floor. If the same view against the same reference has reached three
consecutive non-improving rounds, stop the edit loop and decide. Inside a
Workshop run the Workshop Manager owns that decision (ADR 0074): an explicit
`--likeness-accept-mismatch "<why this measured mismatch is acceptable>"` on
the final runner can then unblock delivery, and the run reports the label,
score and reason to the person when it ends. The runner also writes them to
`measure/likeness-acceptance.json`, bound to the exact pipeline record. The raw likeness gate remains a
failure; `measure/verification-pipeline.md` reports `PASS (1 accepted failing
gate)` and records the score and exact reason. Errors, an unaccepted regression,
or a fresh improving row still fail. If the fresh gate passes, the runner warns
that the flag was unnecessary and records no acceptance note. It also runs
`render_views.py --compare-step`; a drift finding means the exported STEP is
not the geometry the source currently builds.

A usable whole-object viewpoint must contain the whole extracted silhouette.
If the subject touches an image boundary, the likeness tools reject it (why:
`wiki show silhouette-likeness#clipped-references-and-burnt-in-labels`).
Keep clipped frames for qualitative review and use a complete view for the
numeric gate. The standalone tools expose `--allow-clipped-reference` only for
an explicitly scoped partial-feature comparison; the integrated final workflow
does not use that escape hatch.

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

**Read the solid's topology; do not sample it.** This audit is project code,
so nothing bounds its cost. Reach for `edges()`/`faces()` filtered by
`geom_type`, radius, axis or position first; a `Location`/bbox read second;
`is_inside` and boolean intersections last, with a call budget in mind. The
measured numbers — one ledger row at 61.1 s probing versus 0.004 s reading
edges, 62 % of a whole gate suite, and why `is_inside` cost grows with face
count — are in `skills/wiki/pages/image-reading/landmark-audit-topology.md`
(`wiki show landmark-audit-topology`).

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
