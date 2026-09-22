# Thickness and hollow

`artifacts/make/r0001/product/mintfin/part_head_front.step.py --nozzle .4 --min-wall 1.2 --report artifacts/make/r0001/product/mintfin/measure/wish-thickness-head_front.md`

part_head_front.step.py: 52.28 cm3 solid, grid 0.200 mm (338x235x148), 225533 surface samples, thickness resolved to 0.100 mm

| check | status | detail |
|---|---|---|
| wall >= 1.20 mm (+/-0.10) | PASS | 0.1% of surface below (106 of 225533 samples); thinnest 0.20 mm at (21.8, 20.1, 20.0) in 52 region(s); no region is a wall, 52 taper(s) at feature edges (0.05% of surface, budget 2%); 39 more within measurement error of the limit |
| thickness distribution | PASS | median 24.20 mm, p95 60.20 mm, max 66.60 mm |
| hollowable at 1.20 mm wall | WARN | 41.60 of 52.28 cm3 (80%) in 1 pocket(s) |
| filament that would save | PASS | 6.24 cm3, 7.7 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.60 mm | (8.2, -18.2, 28.0) | 4 | 0.9 | 3.1 | 0.30 |
| 2 | taper | 0.20 mm | (-8.9, 15.8, 20.9) | 11 | 0.4 | 5.5 | 0.08 |
| 3 | taper | 0.20 mm | (-4.1, -18.3, 28.2) | 7 | 0.3 | 1.2 | 0.24 |
| 4 | taper | 0.30 mm | (-26.9, -13.4, 27.1) | 6 | 0.3 | 2.9 | 0.09 |
| 5 | taper | 0.40 mm | (-19.0, 19.2, 20.2) | 8 | 0.2 | 3.8 | 0.05 |
| 6 | taper | 0.20 mm | (-24.5, 16.7, 20.7) | 5 | 0.2 | 1.5 | 0.11 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
