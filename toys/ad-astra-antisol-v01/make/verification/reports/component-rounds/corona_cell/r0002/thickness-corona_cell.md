# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_corona_cell.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/corona_cell/r0002/thickness-corona_cell.md`

part_corona_cell.step.py: 3.36 cm3 solid, grid 0.133 mm (262x262x80), 194148 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | FAIL | 17.5% of surface below (30977 of 194148 samples); thinnest 0.13 mm at (4.2, 0.6, 2.3) in 3 region(s); 1 wall(s) (widest band 14.63 mm), 2 taper(s) at feature edges (0.00% of surface, budget 2%); 233 more within measurement error of the limit |
| thickness distribution | PASS | median 2.93 mm, p95 34.20 mm, max 46.00 mm |
| hollowable at 1.20 mm wall | WARN | 0.26 of 3.36 cm3 (8%) in 5 pocket(s), 1 too small to shell |
| filament that would save | PASS | 0.04 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.13 mm | (4.2, 0.6, 2.3) | 30972 | 652.3 | 44.6 | 14.63 |
| 2 | taper | 0.47 mm | (15.8, 15.5, 10.0) | 4 | 0.1 | 0.6 | 0.11 |
| 3 | taper | 0.60 mm | (-15.7, 15.7, 10.0) | 1 | 0.0 | 0.0 | 0.13 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
