# Rainward Corona CAD

Source correction of the cloned Rainward Lowflow baseline. Units mm, XY bed,
+Z up, every printable part with its bed datum at Z0.

## File map

| Path | What it holds |
|---|---|
| `params.py` | every dimension, colour and filament name, with a provenance tag per value |
| `validation.py` | the algebraic parameter checks; `parts/__init__.py` runs them before any geometry |
| `profiles.py` | kernel-free plan outlines: lane sectors, flame tongues, the hero loop |
| `features/` | small reusable solids: the drafted boundary wedge, the capsule marker, the locating key |
| `parts/body.py` | the Sun body: deck, corona rim, 24 lane pockets, centre bar, markers |
| `parts/tile.py` | one lane tile, in assembly pose and in print pose |
| `parts/counter.py` | the two preserved counter silhouettes |
| `assemblies/product.py` | placement only: setup, before, after and board states |
| `rainward.step.py` | the single combined review entry, `PRINTABLE = False` |
| `part_*.step.py` | one printable entry per occurrence, 55 of them |
| `measure/` | the project's own audits and their JSON records |
| `snap/` | the canonical render family and the exact-state STEPs it was made from |

Rebuild everything with the materialized CAD `gen` tool on explicit targets:
the 55 part entries plus the combined entry, with `--write --force`. The
combined entry reads `RAINWARD_STATE` (`setup`, `before`, `after`, `board`) and
`RAINWARD_TONE` (`colour`, `neutral`); `measure/render_evidence.py` writes the
exact-state STEPs and the whole render family from it.

`params.py` changes the shared closure for every entry, so regenerate all
targets explicitly after touching it and rebuild once more before trusting the
bytes: the first rebuild after a shared-library edit can still serve the
previous geometry.

## Board

Outer plan 190 × 190 mm over the radius-90 disc; the corona ring takes the
envelope to 188.232 × 191.437 mm, inside the 194 mm limit. Deck 8.0, lane tile tops
8.8, centre bar top 9.0 over a radius-24 circle, boundary markers to 9.0.
Twenty-four lane pockets with floors at 6.0 carry 2.8 mm tiles. The body left
between two pockets is 0.8 mm where it is exposed at 8.0, and 1.6 mm at the
four bank boundaries; it drafts 0.6 mm wider per side down to the pocket floor,
and the tiles carry the matching draft, so no boundary is a 0.8 mm fin. The
pockets stop at radius 86.5 and the rim stays a continuous ring whose top sits
at 7.8; the outer 3.5 mm of each tile is a 1.0 mm lip that laps it.

Lane axes are the preserved `-75 + 15(p-1)` degrees. Five radial stations at
85, 72, 59, 46 and 33, three aligned layers, fifteen counters per lane. Four
capsule markers, 10 × 0.8, centred at radius 65 on the 24/1, 6/7, 12/13 and
18/19 boundaries.

## Corona rim

Twenty prominences: nineteen flame tongues and one hero loop. Roots start at
radius 87.2, inside the rim ring and clear of every pocket, so no pocket ever
cuts one. Tips reach 3.0 to 6.6 mm beyond radius 90, the thinnest tip is
1.3 mm, all sweep the same rotational direction, and the hero arch encloses one
closed 88 mm² window against the disc edge. The ring is flat in the deck plane
with its top flush at 8.0.

## Counters

12 × 8 × 4 mm, the original Bezier control points unchanged, flat parallel top
and bottom. The split-tail builder still normalises sub-picometer endpoint
roundoff before extrusion so repeated builds do not alternate STEP number
formatting; the curves and dimensions are untouched.

--bed 200x200x200

## What the measurements say

`measure/verification-pipeline.md` is the final verifier's report.
`measure/fit-audit.json` measures where every counter lands on its own tile top.
`measure/corona-plan-audit.json` audits the rim's plan.
`measure/greyscale-tone.json` and `measure/neutral-countability.json` are the
colour and single-material evidence. All of it is digital: nothing here
establishes printed fit, retention, handling, stack stability or durability,
and no physical test was run. Motion is unverified; this set has no coupled
mechanism.
