# Detecting nonconformance

Read this when a round's run is `complete` and you need its findings. Each
layer compares the archive with the Design Contract and emits **findings**. A
finding has a stable id, and the loop's no-progress rule compares those ids,
so the same defect must get the same id in every round.

| Finding id | Layer | Raised when |
|---|---|---|
| `envelope` | geometry | assembled extents disagree with `envelope_mm` |
| `extents:<geometry>` | geometry | a Component built to the geometry disagrees with `extents_mm` |
| `print:<geometry>` | print | a print gate of a Component built to it did not pass in final verification, or no row proves it ran |
| `count:<geometry>` | geometry | the number of Components built to it differs from `count` |
| `unmapped:<geometry>` | geometry | no Component could be mapped to the geometry at all |
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
  When the contract grants a hidden-joint allowance (a section that lets
  Make extend a part along a joint axis by at most N mm), a measured extent
  may exceed its contract value by up to N on that one axis. Record the
  excess and the joint from Make's `GEOMETRY-NOTES.md` as the evidence; a
  larger excess, an excess on a second axis, or one the notes do not name is
  still a finding.
- `count:<geometry>`: the number of Components mapped to the geometry, against
  `count`. Say what the count was read from.
## Print (Make's own gates)

Read `<toy-dir>/make/verification/CAD-GATE.json`, final verification's
record: a Markdown table with one row per command and its result. For each
mapped Component, find the `check_mesh`, `check_overhang` and
`check_thickness` rows that name its source (`part_<role>.step.py`, or the
report path `measure/overhang-<role>.md` and `measure/thickness-<role>.md`;
for a kit Component, the rows of each of its Parts). Raise
`print:<geometry>` when any of them is not `rc=0`, quoting the row, and as
*unverified* when one of the three is missing. Do not run the gates
yourself and do not measure walls against `wall_min_mm`: Make gates every
wall at the nozzle's print minimum, and its result is the one this layer
reports.

## No likeness score

Nothing scores silhouettes. ADR 0076 removed IoU from Make: a Component
passes on its Component Reviewer's agreement or on a recorded Component
Acceptance, and the blind review judges the assembly against its reference.
Do not run `render_views.py --match`. Copy each Component Acceptance and
Reference Conflict from the run's receipt (`workshop status --json`) into
`notes` in `findings.json`, never into `findings`: Make already reports
them, and a fix round cannot turn a reviewer's disagreement into a pass.

## Motion (deterministic sweep)

When the contract has a moving part, read the `check_motion` row of
`<toy-dir>/make/verification/CAD-GATE.json`. Raise `motion` when that row is
`skipped`, timed out, or anything other than a pass, and quote the row as the
evidence. A skipped or unfinished sweep is *unverified*, never clear, and the
requirement rows for the motion do not pass without it. Broken God v01
recorded every mechanism requirement as matching while its sweep had timed out
three times and its final check had been skipped.

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
  "notes": ["Component Acceptance: world-disc after 5 Shape Rounds (receipt)"],
  "passed": ["envelope", "print:world-disc"]
}
```

Every contract check appears exactly once, either in `findings` or in `passed`.
Detection is complete when that holds.
