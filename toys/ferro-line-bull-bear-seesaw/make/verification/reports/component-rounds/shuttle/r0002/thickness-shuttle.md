# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_shuttle.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/shuttle/r0002/thickness-shuttle.md`

part_shuttle.step.py: 5.48 cm3 solid, grid 0.133 mm (1175x290x27), 286534 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | FAIL | 0.4% of surface below (1210 of 286534 samples); thinnest 0.20 mm at (-0.1, -18.7, 0.3) in 1 region(s); 1 wall(s) (widest band 4.88 mm); 120 more within measurement error of the limit |
| thickness distribution | PASS | median 2.93 mm, p95 16.00 mm, max 156.00 mm |
| hollowable at 1.20 mm wall | WARN | 0.65 of 5.48 cm3 (12%) in 1 pocket(s) |
| filament that would save | PASS | 0.10 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.20 mm | (-0.1, -18.7, 0.3) | 1210 | 23.5 | 4.8 | 4.88 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
