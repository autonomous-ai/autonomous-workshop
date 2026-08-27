# Image-derived CAD verification

Read this file when a CAD project originates from photographs, illustrations,
or a build spec produced by `image-to-cad`.

Geometry soundness and visual fidelity are separate claims. The integrated
final workflow is:

```bash
CADGEN_WARM=1 python "$CAD_SKILL_ROOT/scripts/verify_project" <project-dir> --fresh --exports \
  --image-derived --unpowered \
  --likeness-ref hero=ref/hero.png \
  --likeness-ref side=ref/side.png
```

Replace `--unpowered` with `--powered` whenever the approved spec declares a
functional electrical load. The mode requires one explicit classification;
`--powered` also requires `measure/power.json`.

Reference paths must remain inside the project. Give every usable viewpoint;
do not choose only the image the model happens to match best. The runner writes
the orthogonal review set and searched reference poses under `snap/`, records
the cameras in `snap/poses.json`, writes `measure/likeness.md`, and fails when
any pair is below the 0.90 delivery floor. The integrated runner never lowers
that floor. If the same view against the same reference has reached three
consecutive non-improving rounds, stop the edit loop and put the decision back
to the user. An explicit
`--likeness-accept-mismatch "<why this measured mismatch is acceptable>"` on
the final runner can then unblock delivery. The raw likeness gate remains a
failure; `measure/verification-pipeline.md` reports `PASS (1 accepted failing
gate)` and records the score and exact reason. Errors, an unaccepted regression,
or a fresh improving row still fail. If the fresh gate passes, the runner warns
that the flag was unnecessary and records no acceptance note. It also runs
`render_views.py --compare-step`; a drift finding means the exported STEP is
not the geometry the source currently builds.

A usable whole-object viewpoint must contain the whole extracted silhouette.
If the subject touches an image boundary, the likeness tools reject it: their
height normalisation cannot tell a cropped object from a short one, so both the
IoU and the searched camera would answer the crop rather than the geometry.
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

**Read the solid's topology; do not sample it.** This audit is project code, so
nothing in the toolchain bounds its cost — and "probe the solid until I find the
surface" is the easiest way to make one ledger row cost more than every
deterministic gate put together. Measured on a six-part pump:

| the row: *count the four ridge crests on each hose barb* | cost |
|---|---|
| walk a radial probe along each barb, bisecting for the outer radius — 4 400 `Shape.is_inside` calls | **61.1 s** |
| read the crest circles off the solid's own edges — `geom_type == CIRCLE`, radius, centre on the port axis | **0.004 s** |

61.1 s was **62 % of that project's entire gate suite**, on a model whose
`inspect validate` costs 2.2 s and whose `inspect interfere` costs 1.0 s. The
topology read is not merely faster, it is a better measurement: it *identifies*
each crest instead of sampling near one, and it stays falsifiable — sabotaging
the ridge count to 3 makes it report 3, and removing the crest land makes it
report 2.

Two numbers behind that, worth knowing before writing a probe at all:

- **`is_inside` scales with face count.** On the same assembly it cost 0.38 ms
  on the 34-face rotor and 2.9–15 ms on the 108-face housing. Adding the
  fillets that fixed a `check_thickness` failure tripled the housing's faces —
  and quadrupled a landmark row that had nothing to do with them.
- **A bisection is not the fix.** Replacing a 130-step linear walk with a
  9-step bisection cut that row by 5× and left it the slowest thing in the run.
  Changing *what* is measured beat changing *how* by three more orders of
  magnitude.

So reach for `edges()`/`faces()` filtered by `geom_type`, radius, axis or
position first; a `Location`/bbox read second; `is_inside` and boolean
intersections last, and then with a call budget in mind.

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
