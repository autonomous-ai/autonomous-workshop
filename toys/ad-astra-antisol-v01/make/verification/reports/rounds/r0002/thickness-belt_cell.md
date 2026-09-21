# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_belt_cell.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0002/thickness-belt_cell.md`

part_belt_cell.step.py: 6.11 cm3 solid, grid 0.133 mm (256x256x50), 154065 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (3 of 154065 samples); thinnest 0.13 mm at (-12.7, 15.6, 5.5) in 2 region(s); no region is a wall, 2 taper(s) at feature edges (0.00% of surface, budget 2%); 1 more within measurement error of the limit |
| thickness distribution | PASS | median 6.00 mm, p95 33.47 mm, max 45.27 mm |
| hollowable at 1.20 mm wall | WARN | 2.84 of 6.11 cm3 (46%) in 1 pocket(s) |
| filament that would save | PASS | 0.43 cm3, 0.5 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.47 mm | (11.8, -6.6, 5.4) | 2 | 0.1 | 0.1 | 0.48 |
| 2 | taper | 0.13 mm | (-12.7, 15.6, 5.5) | 1 | 0.0 | 0.0 | 0.12 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
