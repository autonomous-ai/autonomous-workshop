# Image-derived CAD verification

Read this file when a CAD project originates from photographs, illustrations,
or a build spec produced by `image-to-cad`.

Geometry soundness and visual fidelity are separate claims. The integrated
final workflow is:

```bash
CADGEN_WARM=1 python "$CAD_SKILL_ROOT/scripts/verify_project" <project-dir> --fresh --print-gates \
  --image-derived --unpowered
```

Replace `--unpowered` with `--powered` whenever the approved spec declares a
functional electrical load. The mode requires one explicit classification;
`--powered` also requires `measure/power.json`.

The mode runs spec/source reconciliation (`measure/check_spec.py`), landmark
coverage (`measure/check_landmarks.py`), the orthogonal front/right/top/iso
silhouettes under `measure/verification-views/`, and `render_views.py
--compare-step`; a drift finding means the exported STEP is not the geometry
the source currently builds. The run never writes under `snap/`: `snap/iso.png`
is the Hero the signature review binds by hash, so verifying leaves it, and
every other review-bound image, byte-identical (issue #109).

No silhouette score is computed and no IoU floor gates delivery: the likeness
gate and its `--likeness-ref`, `--likeness-min`, `--likeness-accept-mismatch`,
`--likeness-accept-regression` and `--search-fov` flags are gone, and the
runner refuses them. Whether the model looks like its references is a reviewed
judgement, not a number.

Inside a Workshop run with a Design Contract, every sealed `geometry:<id>`
image is accounted for by that Component's current round, which `make_round`
reports. The round passes when its build and print checks pass and an
independent reviewer (never the Workshop Manager) recorded that the model
looks like its reference. When the shape-repair allowance (5 rounds that
changed the geometry after passing checks) runs out, the reviewer's recorded
review of the last round stands: a disagreement becomes a component
acceptance. A sealed component image with no such round fails the final run
with a `component review` row naming `make_round --component
part_<role>.step.py`. Sealed `assembly` images are shown to the assembly's
blind review, not scored here.

Every image-derived final run in Contract Mode writes
`measure/component-acceptance.json` beside the pipeline record, bound to its
sha256, with one entry per accepted Component (an empty list when none):
`{"label": "geometry:<id>", "scope": "component:<role>", "reviewer", "shape_rounds",
"reason", "accepted_by": "workshop-manager"}`. The run reports each acceptance
to the person when it ends.

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
their own target because the overall form can hide their omission.

The audit must fail on an omitted ledger item. It may share project builders,
but it must measure the returned geometry rather than restating the arithmetic
that created it. Keep exact distances and alignments in
`inspect measure/align/frame`.

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

If a review difference or landmark check causes a source change, reconcile the
spec in the same edit. A final run with stale prose is a failed run even when
the source geometry improved.
