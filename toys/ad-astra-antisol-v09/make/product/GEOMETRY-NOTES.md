# Geometry verification: what was measured

The integrated geometry inspection **ran to completion and passed**. This file
records exactly what that covers, because an earlier draft of it — written
while the pass was still being cut short by the session boundaries this run hit
repeatedly — said the opposite. It was wrong in the safe direction, and it is
corrected here rather than quietly deleted.

## The result

`cad/measure/verification-pipeline.md`, final mode, **PASS, exit 0, 722.83 s**,
on a 200 x 200 x 200 mm bed. Eleven steps: seven ran and passed, three are not
applicable and are recorded as not run rather than as passed, one is the
signature-review note.

| step | result | seconds |
|---|---|---:|
| signature review (schema 6) | note | 0.00 |
| `check_layout` | passed | 0.11 |
| `gen` — every STEP regenerated from source | passed | 279.87 |
| `check_fit` | passed | 14.30 |
| the project's own fit ledger | passed | 0.03 |
| `check_spec_numbers` | passed | 2.09 |
| `check_spec_format` | passed | 0.06 |
| `check_mount` | NOT RUN — no bought part is declared seated | 0.00 |
| `check_power` | NOT RUN — no powered system is declared | 0.00 |
| `check_motion` | NOT RUN — disabled by Make motion policy | 0.00 |
| `inspect` batch | passed | 426.37 |

## What the inspection batch covered

`cad/measure/geometry-inspection.json` records **51 checks, every one passed**,
with `status: passed`:

- **`validate:assembly`** — topology, closed shells, no self-intersection and
  positive volume on every one of the 236 occurrences of the whole set.
- **`interfere:assembly`** — the question nothing else in the toolchain can
  answer: do any two of those 236 occurrences occupy the same space? They do
  not.
- **`refs:assembly`** — scale, labels, planes and placement references.
- **`refs` and `validate` on all 24 printed parts individually**, including
  both corrected Uranus pieces.

## What is still NOT claimed

**Motion is unverified, not passed.** The operator's `check_motion` is false
for this run, so the motion gate did not run. Nothing in this set moves against
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
isolated component rounds — 24 of 24 on each, with no region anywhere needing
support and no bridges. Those reports are at
`cad/measure/thickness-<role>.md` and `cad/measure/overhang-<role>.md`. They
are measurements and predictions for that nozzle, not a print.
