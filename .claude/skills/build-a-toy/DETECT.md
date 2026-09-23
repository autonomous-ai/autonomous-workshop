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
| `requirement:<id>` | requirements | the requirement fails, or nothing ever reviewed it |

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

## Requirements (review coverage, then a blind read of the gaps)

Read `<toy-dir>/make/verification/renders/SIGNATURE-REVIEW.json`. In legacy
mode the Manager wrote its `critical_form_requirements`, so the list shows
what was checked, not what should have been.

1. For each contract requirement, find the review row that covers it, and quote
   that row's `requirement` text as the match. If no row covers it, the
   requirement was **never reviewed**.
2. Take a covered row with `matches: true` as the run's own evidence, and say
   in the report that it is Manager-listed.
3. Give every never-reviewed requirement a blind read. Hand a fresh subagent
   only the images: `make/verification/renders/iso.png` and `signature.png`
   for an assembly requirement, or the Component's front, top and iso views for
   a geometry requirement (`render_views.py <copy> --view front --view top
   --view iso`). Do not tell it the Wish, the contract or the intended answer.
   Ask one narrow question about what it sees in the region the requirement
   concerns. Keep its answer verbatim. Only then compare the answer with the
   requirement. A requirement the answer does not clearly satisfy is a
   `requirement:<id>` finding.

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
