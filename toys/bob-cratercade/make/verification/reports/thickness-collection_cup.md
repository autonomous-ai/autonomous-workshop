# Thickness and hollow

`part_collection_cup.step.py --nozzle 0.4 --report measure/thickness-collection_cup.md`

part_collection_cup.step.py: 32.12 cm3 solid, grid 0.264 mm (255x376x122), 311476 surface samples, thickness resolved to 0.132 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.13) | PASS | 0.1% of surface below (180 of 311476 samples); thinnest 0.26 mm at (13.9, 56.6, 30.5) in 6 region(s); no region is a wall, 6 taper(s) at feature edges (0.06% of surface, budget 2%); 29 more within measurement error of the limit |
| thickness distribution | PASS | median 2.90 mm, p95 30.89 mm, max 96.36 mm |
| hollowable at 1.20 mm wall | WARN | 3.98 of 32.12 cm3 (12%) in 3 pocket(s) |
| filament that would save | PASS | 0.60 cm3, 0.7 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.26 mm | (13.9, 56.6, 30.5) | 66 | 4.9 | 14.4 | 0.34 |
| 2 | taper | 0.66 mm | (14.0, 56.9, 5.8) | 42 | 3.1 | 11.1 | 0.28 |
| 3 | taper | 0.40 mm | (11.0, 28.4, 11.3) | 29 | 2.2 | 7.9 | 0.28 |
| 4 | taper | 0.40 mm | (11.0, 28.4, 21.0) | 28 | 2.1 | 9.7 | 0.22 |
| 5 | taper | 0.40 mm | (11.0, 28.3, 7.9) | 13 | 1.0 | 3.8 | 0.26 |
| 6 | taper | 0.40 mm | (11.0, 28.3, 3.7) | 2 | 0.2 | 0.6 | 0.27 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
