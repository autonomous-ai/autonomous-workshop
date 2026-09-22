# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_belt_cell.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/belt_cell/r0002/thickness-belt_cell.md`

part_belt_cell.step.py: 6.38 cm3 solid, grid 0.133 mm (262x262x50), 159228 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (2 of 159228 samples); thinnest 0.13 mm at (-11.1, -6.6, 6.0) in 2 region(s); no region is a wall, 2 taper(s) at feature edges (0.00% of surface, budget 2%); 2 more within measurement error of the limit |
| thickness distribution | PASS | median 6.00 mm, p95 34.27 mm, max 46.40 mm |
| hollowable at 1.20 mm wall | WARN | 2.96 of 6.38 cm3 (46%) in 1 pocket(s) |
| filament that would save | PASS | 0.44 cm3, 0.6 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (-11.1, -6.6, 6.0) | 1 | 0.0 | 0.0 | 0.13 |
| 2 | taper | 0.60 mm | (-16.2, -4.8, 5.9) | 1 | 0.0 | 0.0 | 0.13 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
