# Thickness and hollow

`artifacts/make/r0001/product/cad/part_circle_pulsar.step.py --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-circle_pulsar.md`

part_circle_pulsar.step.py: 2.81 cm3 solid, grid 0.133 mm (170x170x230), 89458 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.2% of surface below (82 of 89458 samples); thinnest 0.73 mm at (0.3, -4.6, 3.5) in 2 region(s); no region is a wall, 2 taper(s) at feature edges (0.18% of surface, budget 2%); 89 more within measurement error of the limit |
| thickness distribution | PASS | median 8.80 mm, p95 22.00 mm, max 30.00 mm |
| hollowable at 1.20 mm wall | WARN | 1.05 of 2.81 cm3 (37%) in 1 pocket(s) |
| filament that would save | PASS | 0.16 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.73 mm | (-0.9, 5.4, 3.4) | 31 | 1.6 | 2.9 | 0.55 |
| 2 | taper | 0.73 mm | (0.3, -4.6, 3.5) | 51 | 1.6 | 3.0 | 0.52 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
