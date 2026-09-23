# Thickness and hollow

`artifacts/make/r0001/product/mintfin/part_leg_left.step.py --nozzle .4 --min-wall 1.2 --report artifacts/make/r0001/product/mintfin/measure/wish-thickness-leg_left.md`

part_leg_left.step.py: 5.19 cm3 solid, grid 0.200 mm (142x107x100), 43202 surface samples, thickness resolved to 0.100 mm

| check | status | detail |
|---|---|---|
| wall >= 1.20 mm (+/-0.10) | PASS | 0.0% of surface below (14 of 43202 samples); thinnest 0.30 mm at (11.9, 9.3, 19.0) in 1 region(s); no region is a wall, 1 taper(s) at feature edges (0.03% of surface, budget 2%); 2 more within measurement error of the limit |
| thickness distribution | PASS | median 14.40 mm, p95 23.80 mm, max 24.20 mm |
| hollowable at 1.20 mm wall | WARN | 3.27 of 5.19 cm3 (63%) in 1 pocket(s) |
| filament that would save | PASS | 0.49 cm3, 0.6 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.30 mm | (11.9, 9.3, 19.0) | 14 | 0.6 | 4.7 | 0.12 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
