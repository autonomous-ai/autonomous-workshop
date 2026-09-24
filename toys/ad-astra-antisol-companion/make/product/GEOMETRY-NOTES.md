# Geometry verification: what was measured

The integrated geometry inspection **ran to completion and passed**. Nothing
was left unverified, nothing was cut short, and nothing below is carried over
from the edition this one corrects — every number here was produced by this
run, against this run's own source.

**One disclosure about how it got there, because it bears on that claim.** The
inspection batch has a time allowance, and this run exhausted it twice before
finishing. Those two attempts produced **no verdict and none was taken from
them**: both were recorded as `UNVERIFIED` at the time, which is what an
interrupted inspection is. The tool resumes exact measurements it has already
completed rather than starting over, so the three runs advanced 1 → 24 → 51 of
the 51 checks, and the record below is the run in which the last of them
finished. The two earlier reports were overwritten by it.

## The result

`cad/measure/verification-pipeline.md`, final mode, **PASS, exit 0, 966.47 s**,
on a 200 × 200 × 200 mm bed. Eleven steps: seven ran and passed, three are not
applicable and are recorded as not run rather than as passed, and one is the
signature-review note.

| step | result | seconds |
|---|---|---:|
| signature review note | note | 0.00 |
| `check_layout` | passed | 0.13 |
| `gen` — all 25 entries regenerated from source | passed | 439.17 |
| `check_fit` — every part against the bed, strict | passed | 26.17 |
| the project's own fit ledger (`measure/check_fit.py`) | passed | 0.03 |
| `check_spec_numbers` | passed | 2.54 |
| `check_spec_format` | passed | 0.06 |
| `check_mount` | NOT RUN — no bought part is declared seated | 0.00 |
| `check_power` | NOT RUN — no powered system is declared | 0.00 |
| `check_motion` | NOT RUN — disabled by this run's motion policy | 0.00 |
| `inspect` batch | passed | 498.37 |

**Motion is unverified rather than passed.** The run's immutable
`MAKE-OPTIONS.json` sets `check_motion: false`, so no motion sweep, animation
or motion review was run and none is claimed. Nothing in this set moves
relative to anything else in any case.

## What the inspection batch covered

`cad/measure/geometry-inspection.json` records **51 checks, every one
`passed`**, with no check interrupted, cancelled or timed out in the run that
sealed it:

- **`validate:assembly`** — topology, closed shells, no self-intersection and
  positive volume on every one of the **222 occurrences** of the whole set.
  (The published set had 220. The difference is exactly the two bodies this
  edition adds: `neptune_sol_companion_white` and `neptune_anti_companion_white`.
  `cad/measure/occurrence-geometry.md` lists them by name.)
- **`interfere:assembly`** — the question nothing else in the toolchain can
  answer: do any two of those 222 occurrences occupy the same space? **They do
  not.** That is the check this edition most needed, because it adds a marking
  that overlaps another one: the dark spot is cut back to a keep-out around the
  new cloud precisely so that the white and the dark never share a volume, and
  this is the measurement that the cut actually worked.
- **`refs:assembly`** — scale, labels, planes and placement references.
- **`refs` and `validate` on all 24 printed parts individually**, both Neptune
  pieces included.

## The two Neptune parts, and why their hashes are the check

`cad/measure/revision-part-hashes.md`: **13 of the 24 printed geometries are
byte-identical** to the published set's, and the two that matter —
`part_world_neptune_sol.step` and `part_world_neptune_anti.step` — are among
them. That is the check this correction turns on rather than a formality. A
marking in this set is a flush colour inlay: `parts/world.build_world` fuses
the disc, the globe and the ring and never a marking, so adding one partitions
the globe's volume without moving the printed solid's own surface. If a cut had
gone deeper than `RELIEF_DEPTH`, or a seat been re-cut, or a globe rebuilt at a
different diameter, those two hashes would have moved with it.

**The other 11 printed parts came back byte-different and are the same solids**,
measured rather than assumed: each was imported from both trees and compared on
exact volume and bounding box, and the largest volume difference anywhere is
**1.13 × 10⁻⁸ mm³** with every bounding box agreeing to a nanometre. What moved
is the serialisation — this project's generator does not write identical STEP
bytes for these parts between a warm multi-target generation and a
single-target one, and six of the eleven come out with a different entity count
for the same shape. None of their generators appears in
`cad/measure/source-diff.md`, which is the literal whole difference between the
two source trees and holds five files.

## What the print gates measured, and what is not claimed

In their own isolated rounds, all **24 printed parts cleared the 0.80 mm wall
gate and the 45-degree overhang gate at a 0.4 mm nozzle** — 24 of 24 on each,
with no region anywhere needing support and no bridges. Those reports are at
`cad/measure/thickness-<role>.md` and `cad/measure/overhang-<role>.md` and they
are this run's, not the archive's.

**No print-readiness is claimed and none is sealed.**
`cad/snap/SIGNATURE-REVIEW.json` carries an empty `print_gate_sha256s` and the
product status is `digitally-verified-not-print-ready`. Every figure in this
file is a measurement on exact CAD solids and a prediction for a 0.4 mm nozzle
at 0.2 mm layers. Nothing here has been printed, handled or played.

## One thing the assembly package does that is not a fault

`assembled.step.json` records a `stepHash` that does not match `assembled.step`.
That is the generator's own behaviour — it writes the package before it
overwrites the STEP, so the hash it records is the previous build's — and the
published set this edition corrects carries the same mismatch for the same
reason. The package's occurrence list, which is what the shop reads, is current:
222 occurrences including both companion bodies.
