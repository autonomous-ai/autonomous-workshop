# Geometry verification: what was measured

The integrated geometry inspection **ran to completion and passed**. Nothing was
left unverified, nothing was cut short, and nothing below is carried over from
the run this revision corrects — every number here was produced by this run.

## The result

`cad/measure/verification-pipeline.md`, final mode, **PASS, exit 0, 786.91 s**,
on a 200 x 200 x 200 mm bed. Eleven steps: seven ran and passed, three are not
applicable and are recorded as not run rather than as passed, one is the
signature-review note.

| step | result | seconds |
|---|---|---:|
| signature review note | note | 0.00 |
| `check_layout` | passed | 0.09 |
| `gen` — all 25 entries regenerated from source | passed | 254.48 |
| `check_fit` | passed | 15.44 |
| the project's own fit ledger (`measure/check_fit.py`) | passed | 0.03 |
| `check_spec_numbers` | passed | 2.24 |
| `check_spec_format` | passed | 0.06 |
| `check_mount` | NOT RUN — no bought part is declared seated | 0.00 |
| `check_power` | NOT RUN — no powered system is declared | 0.00 |
| `check_motion` | NOT RUN — disabled by Make motion policy | 0.00 |
| `inspect` batch | passed | 514.56 |

## What the inspection batch covered

`cad/measure/geometry-inspection.json` records **51 checks, every one passed**,
with `status: passed` and no check interrupted, cancelled or timed out:

- **`validate:assembly`** — topology, closed shells, no self-intersection and
  positive volume on every one of the **224 occurrences** of the whole set.
  (The published set had 236. The difference is exactly the twelve Neptune white
  bodies this revision removed: nine cloud streaks per army became three
  latitude bands per army. `cad/measure/occurrence-geometry.md` lists them by
  name.)
- **`interfere:assembly`** — the question nothing else in the toolchain can
  answer: do any two of those 224 occurrences occupy the same space? **They do
  not.** This is also what settles the one finding the independent critic left
  unresolved — a corona cone that appeared in the isometric render to overhang a
  neighbouring cell. It does not; no pair on this board intersects.
- **`refs:assembly`** — scale, labels, planes and placement references.
- **`refs` and `validate` on all 24 printed parts individually**, both Neptune
  pieces included.

## The two Neptune parts, and why their hashes are the check

`cad/measure/revision-part-hashes.md`: **20 of the 24 printed geometries are
byte-identical** to the published set's, four board panels differ only in a
`NEXT_ASSEMBLY_USAGE_OCCURRENCE` exporter counter with every other line matching
(diffed line by line in this run rather than asserted), and
`part_world_neptune_sol.step` and `part_world_neptune_anti.step` are **also
byte-identical**.

That last one is the check, not a formality. A marking in this set is a flush
colour inlay: it partitions the globe's volume without moving the printed
solid's own boundary. Neptune's white marking went from nine outline bodies to
three latitude bands and its bright companion was dropped; if any of that had
moved the ball's own surface — a lens standing proud, a region cut deeper than
`RELIEF_DEPTH`, an outline reaching past the seat — those two hashes would have
moved with it. They did not.

`cad/measure/neptune-flush.md` measures the same statement directly on the
solids: every point of the `bands` body and every point of the `spot` body lies
at 10.945000 mm from the globe centre against a globe radius of 10.945000 mm, on
both armies, proud by **+0.000000 mm**.

## What is still NOT claimed

**Motion is unverified, not passed.** The operator's `check_motion` is false for
this run, so the motion gate did not run. Nothing in this set moves against
anything else in any case, and no assemblability or working motion is claimed
from skipped evidence.

**This is not a print-readiness claim.** `product.json` seals
`status: digitally-verified-not-print-ready` with `print_ready_claim: false`,
and `cad/snap/SIGNATURE-REVIEW.json` carries an empty `print_gate_sha256s` map.
Every number above is geometry measured on exact CAD solids. Nothing here has
been printed, handled or played, and no physical fit, durability or human
response is claimed.

Separately from the integrated pass, all 24 printed parts cleared the 0.80 mm
wall gate and the 45 degree overhang gate at a 0.4 mm nozzle in their own
rounds in this run — 24 of 24 on each, with no region anywhere needing support
and no bridges. Those reports are at `cad/measure/thickness-<role>.md` and
`cad/measure/overhang-<role>.md`. They are measurements and predictions for that
nozzle, not a print.
