# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/part_pedestal_lid.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/measure/component-rounds/pedestal_lid/r0001/thickness-pedestal_lid.md`

part_pedestal_lid.step.py: 24.74 cm3 solid, grid 0.197 mm (512x505x42), 387501 surface samples, thickness resolved to 0.098 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.10) | FAIL | 0.2% of surface below (769 of 387501 samples); thinnest 0.20 mm at (50.5, -4.0, 5.4) in 6 region(s); 2 wall(s) (widest band 0.81 mm), 4 taper(s) at feature edges (0.15% of surface, budget 2%); 151 more within measurement error of the limit |
| thickness distribution | PASS | median 2.95 mm, p95 37.13 mm, max 98.50 mm |
| hollowable at 1.20 mm wall | WARN | 4.65 of 24.74 cm3 (19%) in 1 pocket(s) |
| filament that would save | PASS | 0.70 cm3, 0.9 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.20 mm | (-28.7, -41.6, 5.4) | 148 | 8.3 | 10.2 | 0.81 |
| 2 | wall | 0.20 mm | (-21.5, 45.9, 5.4) | 143 | 8.0 | 9.8 | 0.81 |
| 3 | taper | 0.20 mm | (-25.8, 40.2, 7.0) | 120 | 6.7 | 9.6 | 0.70 |
| 4 | taper | 0.20 mm | (-27.2, -39.2, 7.0) | 121 | 6.7 | 9.7 | 0.69 |
| 5 | taper | 0.20 mm | (50.5, -4.0, 5.4) | 120 | 6.7 | 10.0 | 0.67 |
| 6 | taper | 0.20 mm | (47.7, -4.6, 7.1) | 117 | 6.4 | 9.6 | 0.67 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
