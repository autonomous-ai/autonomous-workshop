# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_belt_cell.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/belt_cell/r0001/thickness-belt_cell.md`

part_belt_cell.step.py: 6.25 cm3 solid, grid 0.133 mm (262x262x50), 174901 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.3% of surface below (272 of 174901 samples); thinnest 0.27 mm at (-15.2, 5.5, 5.8) in 42 region(s); no region is a wall, 40 taper(s) at feature edges and 2 spot(s) too small to be a wall (0.28% of surface, budget 2%); 139 more within measurement error of the limit |
| thickness distribution | PASS | median 5.93 mm, p95 34.27 mm, max 46.00 mm |
| hollowable at 1.20 mm wall | WARN | 2.65 of 6.25 cm3 (42%) in 1 pocket(s) |
| filament that would save | PASS | 0.40 cm3, 0.5 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.40 mm | (-1.8, -14.0, 5.8) | 21 | 1.1 | 2.3 | 0.49 |
| 2 | taper | 0.60 mm | (1.4, 14.0, 5.6) | 16 | 0.8 | 2.0 | 0.38 |
| 3 | spot | 0.53 mm | (14.0, -14.4, 5.8) | 16 | 0.7 | 0.9 | 0.80 |
| 4 | spot | 0.53 mm | (-13.7, 14.3, 5.8) | 14 | 0.7 | 0.8 | 0.82 |
| 5 | taper | 0.53 mm | (14.4, 13.7, 5.8) | 14 | 0.6 | 0.9 | 0.69 |
| 6 | taper | 0.53 mm | (-14.2, 1.5, 5.8) | 15 | 0.6 | 2.1 | 0.30 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
