# Detecting nonconformance

Read this when a round's run is `complete` and you need its findings. Each
layer compares the archive with the Design Contract and emits **findings**. A
finding has a stable id, and the loop's no-progress rule compares those ids,
so the same defect must get the same id in every round.

| Finding id | Layer | Raised when |
|---|---|---|
| `envelope` | geometry | assembled extents disagree with `envelope_mm` |
| `extents:<geometry>` | geometry | a Component built to the geometry disagrees with `extents_mm` |
| `wall:<geometry>` | geometry | thinnest wall is below `wall_min_mm`, or no report proves it |
| `count:<geometry>` | geometry | the number of Components built to it differs from `count` |
| `unmapped:<geometry>` | geometry | no Component could be mapped to the geometry at all |
| `likeness:<ref-stem>` | likeness | IoU below 0.90, or the score could not be produced |
| `requirement:<id>` | requirements | the review has no contract-bound row for it (should not happen for a run started with `--contract`) |

Anything that could not be measured is a finding, never a pass. That rule is
the whole reason this skill exists.

## Read only copies

`workshop fix` refuses an archive that has even one file outside its manifest,
and the error does not name the file. Measuring in place can leave a
`__pycache__` or a tool cache behind. Copy what you measure into the round's
scratch directory first, and never write inside `toys/<slug>/` or a run
workspace:

```bash
R=<contract-dir>/build-a-toy/r<NN>/detect      # this round's scratch
mkdir -p "$R/step" && cp <toy-dir>/make/models/assembled.step <toy-dir>/make/models/cad/*.step "$R/step/"
```

Run the commands below from the Workshop repository root, with `uv run`.

## Geometry (deterministic)

Measure each copied STEP:

```bash
uv run python src/workshop/make/skills/cad/scripts/inspect refs "$R/step/<file>.step" --facts
```

Read `tokens[0].entryFacts.size`: the `[x, y, z]` extents in mm, taken from
the exact STEP with no rebuild. Sort both the measured extents and the
contract's extents in descending order, then compare them pairwise. Axis order
is Make's choice, not the contract's. Each pair must agree within
**±0.05 mm**. That tolerance describes the instrument, not the design. The
contract's numbers are decisions, not estimates.

- `envelope`: `assembled.step` against `envelope_mm`.
- `extents:<geometry>`: map each geometry to the Component STEPs built to it,
  using `part_<role>` names, `make/product.json` and the extents. Record the
  mapping and the evidence for it in `findings.json`. Compare every mapped
  Component. If nothing maps, raise `unmapped:<geometry>` instead.
- `count:<geometry>`: the number of Components mapped to the geometry, against
  `count`. Say what the count was read from.
- `wall:<geometry>`: read the thinnest wall from
  `<toy-dir>/make/verification/reports/thickness-<role>.md` for each mapped
  Component. If the report is missing, raise the finding as *unverified*.

## Likeness (deterministic score)

Score each contract reference against the geometry it `shows`. Use
`assembled.step` for `assembly`, and one mapped Component copy for
`geometry:<id>`:

```bash
uv run python src/workshop/make/skills/image-to-cad/scripts/render_views.py \
  "$R/step/<file>.step" --match <contract-dir>/<ref-file> --label <ref-stem> \
  --min 0.90 --search-fov 0,25,40 -o "$R/likeness/<ref-stem>" --json
```

Read `views[0].iou`. At or above 0.90 passes. A `MASK SUSPECT` stop means the
reference image's mask is broken, not the model. Flatten the image with
`image-to-cad/scripts/ref_silhouette.py` and score again. Record both scores,
and do not raise the finding against the toy for a mask problem.

## Requirements (already contract-bound review)

Every round runs under `--contract`, so the host's finalizer already refused
any proposal whose review did not carry, in the contract's own order, one row
per assembly-scoped requirement (`critical_form_requirements`) and one row
per geometry-scoped requirement (`geometry_form_requirements`, when the
contract has any), each with matching text and `matches: true`. A round that
reached `complete` has therefore already had every requirement reviewed and
passed by the run itself — there is no Manager-written list to re-derive
coverage from, and no gap to give a blind read.

Read `<toy-dir>/make/verification/renders/SIGNATURE-REVIEW.json`. For each
contract requirement, in order, take its matching row — `critical_form_requirements`
for an assembly-scoped requirement, `geometry_form_requirements` for a
geometry-scoped one — and record `passed: "requirement:<id>"` in
`findings.json`, quoting that row's `blind_evidence` as the evidence. If a
row is somehow missing for a requirement, that is itself a `requirement:<id>`
finding: it means this run did not, in fact, start under `--contract` with
this exact contract, and no other layer would catch that.

## Output

Write `<contract-dir>/build-a-toy/r<NN>/findings.json`:

```json
{
  "round": 1,
  "toy_dir": "toys/ad-astra-antisol-v02",
  "mapping": {"world-disc": ["part_world_mercury_sol", "..."]},
  "findings": [
    {"id": "extents:world-disc", "contract": [30, 30, 6], "measured": [30.0, 30.0, 4.2],
     "evidence": "inspect entryFacts.size of part_world_mercury_sol.step", "unverified": false}
  ],
  "passed": ["envelope", "likeness:ref-01-hero"]
}
```

Every contract check appears exactly once, either in `findings` or in `passed`.
Detection is complete when that holds.
