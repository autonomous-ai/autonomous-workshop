# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_landing_ramp.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0002/thickness-landing_ramp.md`

part_landing_ramp.step.py: 39.61 cm3 solid, grid 0.306 mm (155x342x201), 147261 surface samples, thickness resolved to 0.153 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.15) | FAIL | 0.7% of surface below (995 of 147261 samples); thinnest 0.31 mm at (0.5, 1.4, 22.7) in 4 region(s); 1 wall(s) (widest band 2.81 mm), 3 taper(s) at feature edges (0.05% of surface, budget 2%); 145 more within measurement error of the limit |
| thickness distribution | PASS | median 5.81 mm, p95 31.78 mm, max 75.79 mm |
| hollowable at 1.20 mm wall | WARN | 23.73 of 39.61 cm3 (60%) in 1 pocket(s), 14 too small to shell |
| filament that would save | PASS | 3.56 cm3, 4.4 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.31 mm | (0.5, 1.4, 22.7) | 928 | 88.8 | 31.6 | 2.81 |
| 2 | taper | 0.46 mm | (35.9, 102.9, 26.6) | 62 | 6.7 | 26.4 | 0.25 |
| 3 | taper | 0.31 mm | (45.7, 103.2, 0.9) | 3 | 0.4 | 1.2 | 0.31 |
| 4 | taper | 0.46 mm | (45.9, 102.9, 30.1) | 2 | 0.3 | 1.4 | 0.18 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
