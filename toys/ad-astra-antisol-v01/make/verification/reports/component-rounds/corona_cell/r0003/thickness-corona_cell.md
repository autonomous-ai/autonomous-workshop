# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_corona_cell.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/corona_cell/r0003/thickness-corona_cell.md`

part_corona_cell.step.py: 3.44 cm3 solid, grid 0.133 mm (262x262x80), 175682 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | FAIL | 7.4% of surface below (12060 of 175682 samples); thinnest 0.33 mm at (-9.9, -10.2, 2.6) in 18 region(s); 16 wall(s) (widest band 2.18 mm), 2 taper(s) at feature edges (0.00% of surface, budget 2%) |
| thickness distribution | PASS | median 2.93 mm, p95 34.20 mm, max 45.93 mm |
| hollowable at 1.20 mm wall | WARN | 0.30 of 3.44 cm3 (9%) in 5 pocket(s), 8 too small to shell |
| filament that would save | PASS | 0.04 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.33 mm | (-14.6, -0.2, 2.6) | 967 | 19.4 | 9.4 | 2.05 |
| 2 | wall | 0.33 mm | (9.7, 10.1, 2.6) | 963 | 19.2 | 9.0 | 2.13 |
| 3 | wall | 0.33 mm | (-0.3, 13.9, 2.6) | 952 | 19.1 | 9.4 | 2.04 |
| 4 | wall | 0.33 mm | (-9.9, -10.2, 2.6) | 941 | 19.0 | 9.5 | 2.01 |
| 5 | wall | 0.33 mm | (0.0, -15.1, 2.6) | 909 | 18.7 | 9.2 | 2.04 |
| 6 | wall | 0.33 mm | (14.5, 0.2, 2.6) | 929 | 18.6 | 9.2 | 2.03 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
