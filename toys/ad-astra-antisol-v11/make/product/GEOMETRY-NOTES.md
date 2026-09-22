# Geometry verification: what was measured

The integrated geometry inspection **ran to completion and passed**. Nothing was
left unverified, nothing was cut short, and nothing below is carried over from
the run this revision corrects — every number here was produced by this run.

One disclosure about how it got here, because it bears on that claim. An earlier
attempt at this pipeline was interrupted part-way through by a session ending.
**That run produced no verdict and none was taken from it.** An interrupted
inspection has no result; the run recorded below started from the beginning and
finished. The only artefact the interrupted attempt left was a preflight refusal
record, which this run overwrote.

## The result

`cad/measure/verification-pipeline.md`, final mode, **PASS, exit 0, 652.29 s**,
on a 200 x 200 x 200 mm bed. Eleven steps: seven ran and passed, three are not
applicable and are recorded as not run rather than as passed, one is the
signature-review note.

| step | result | seconds |
|---|---|---:|
| signature review note | note | 0.00 |
| `check_layout` | passed | 0.12 |
| `gen` — all 25 entries regenerated from source | passed | 237.43 |
| `check_fit` | passed | 14.68 |
| the project's own fit ledger (`measure/check_fit.py`) | passed | 0.03 |
| `check_spec_numbers` | passed | 2.25 |
| `check_spec_format` | passed | 0.06 |
| `check_mount` | NOT RUN — no bought part is declared seated | 0.00 |
| `check_power` | NOT RUN — no powered system is declared | 0.00 |
| `check_motion` | NOT RUN — disabled by Make motion policy | 0.00 |
| `inspect` batch | passed | 398.06 |

## What the inspection batch covered

`cad/measure/geometry-inspection.json` records **51 checks, every one passed**,
with `status: passed` and no check interrupted, cancelled or timed out:

- **`validate:assembly`** — topology, closed shells, no self-intersection and
  positive volume on every one of the **220 occurrences** of the whole set.
  (The published set had 224. The difference is exactly the four beige bodies
  this revision removed: one polar hood at each pole of each Uranus piece.
  `cad/measure/occurrence-geometry.md` lists them by name.)
- **`interfere:assembly`** — the question nothing else in the toolchain can
  answer: do any two of those 220 occurrences occupy the same space? **They do
  not.** This is also what settles the findings the independent critic raised
  about pieces, rings and flames appearing to collide on the board: they do not,
  and what an isometric render shows at those cells is two parts overlapping in
  projection rather than in space.
- **`refs:assembly`** — scale, labels, planes and placement references.
- **`refs` and `validate` on all 24 printed parts individually**, both Uranus
  pieces included.

## The two Uranus parts, and why their hashes are the check

`cad/measure/revision-part-hashes.md`: **20 of the 24 printed geometries are
byte-identical** to the published set's, four board panels differ only in a
`NEXT_ASSEMBLY_USAGE_OCCURRENCE` exporter counter with every other line matching
(diffed line by line in this run rather than asserted), and
`part_world_uranus_sol.step` and `part_world_uranus_anti.step` are **also
byte-identical** at `7eccfab310b21fef` and `d993913622975638`.

That last one is the check, not a formality. A marking in this set is a flush
colour inlay: it partitions the globe's volume without moving the printed
solid's own boundary. Removing one therefore stops partitioning the globe and
hands it back the volume the marking held, moving no surface; and repainting the
ring moves one existing solid from one spool to another, moving no surface
either. If either change had touched the ball or the hoop — a cut gone deeper
than `RELIEF_DEPTH`, a ring rebuilt at a different diameter, a seat re-cut —
those two hashes would have moved with it. They did not.

The four panels are worth one more sentence, because the size of their
difference is itself evidence. Their counters read 225, 226, 227 and 228 in the
published set and 221, 222, 223 and 224 here — a shift of exactly four, which is
exactly the four hoods the assembly lost. Nothing about those panels changed
except where they fall in an exporter's numbering.

Measured directly on the solids as well, in `cad/measure/uranus-bare.md`: each
globe now holds its published volume plus both hoods, 5323.412 + 109.5887 +
109.5887 = 5542.588 mm³, with **0.0014 mm³** of residue on both armies; the
marking table for that world is empty; and `world_bodies` returns four roles per
piece and no fifth. In `cad/measure/uranus-ring.md` and
`cad/measure/uranus-mirror.md`: the ring is unmoved to nine decimal places at
54.830480 mm³ and 54.830494 mm³, in the same bounding box, with the 45-degree
gate still measuring 44.3° and 0.0000 mm² over it on both armies, and the two
pieces are exact mirrors. In `cad/measure/saturn-ring-unchanged.md`: Saturn's two
ring occurrences at 574.192167 and 574.192096 mm³, zero delta.

`cad/measure/source-diff.md` carries the entire source difference, pasted whole
rather than summarised — five files, of which two are code, and no dimension
moved in either.

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

**Evidence carried forward rather than re-measured, named so it is not mistaken
for new work.** Twenty of the twenty-four printed geometries are byte-identical
to the published set's, so the reports that measure those parts' surfaces —
Earth's, Mars's, Mercury's, Venus's, Jupiter's, Saturn's and Neptune's atlas,
facing, tone-separation and flush reports — describe solids this run did not
change and are carried forward unchanged. What was regenerated in this run is
everything that could have moved: all 25 entries from source, all 48 print-gate
reports, the whole 51-check inspection, every Uranus measurement, the hash and
occurrence comparisons, the canonical renders, and the independent review.
`cad/measure/retired-hood-evidence.md` says what happened to each piece of
evidence that measured the removed hoods.
