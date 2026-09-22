# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_den_plug.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/den_plug/r0002/thickness-den_plug.md`

part_den_plug.step.py: 9.20 cm3 solid, grid 0.154 mm (282x260x160), 165957 surface samples, thickness resolved to 0.077 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.08) | FAIL | 3.5% of surface below (4898 of 165957 samples); thinnest 0.15 mm at (-11.3, -17.9, 6.9) in 2 region(s); 2 wall(s) (widest band 2.47 mm); 909 more within measurement error of the limit |
| thickness distribution | PASS | median 6.95 mm, p95 34.27 mm, max 35.96 mm |
| hollowable at 1.20 mm wall | WARN | 4.89 of 9.20 cm3 (53%) in 1 pocket(s) |
| filament that would save | PASS | 0.73 cm3, 0.9 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.15 mm | (-17.9, 2.4, 6.8) | 3884 | 113.9 | 46.2 | 2.47 |
| 2 | wall | 0.15 mm | (-11.3, -17.9, 6.9) | 1014 | 30.1 | 24.2 | 1.25 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
