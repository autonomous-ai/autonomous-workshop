# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_lane_03_yellow.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0003/thickness-lane_03_yellow.md`

part_lane_03_yellow.step.py: 2.20 cm3 solid, grid 0.133 mm (399x399x35), 122399 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (335 of 122399 samples); thinnest 0.13 mm at (69.2, 53.8, 0.1) in 2 region(s); no region is a wall, 2 taper(s) at feature edges (0.01% of surface, budget 2%); 5 more within measurement error of the limit |
| thickness distribution | PASS | median 2.80 mm, p95 15.27 mm, max 63.40 mm |
| hollowable at 1.20 mm wall | WARN | 0.23 of 2.20 cm3 (10%) in 1 pocket(s) |
| filament that would save | PASS | 0.03 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (69.2, 53.8, 0.1) | 168 | 0.1 | 0.8 | 0.14 |
| 2 | taper | 0.13 mm | (53.8, 69.1, 0.1) | 167 | 0.1 | 0.8 | 0.11 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
