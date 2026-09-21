# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_lane_04_cocoa_brown.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/thickness-lane_04_cocoa_brown.md`

part_lane_04_cocoa_brown.step.py: 2.22 cm3 solid, grid 0.133 mm (465x332x35), 117482 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (16 of 117482 samples); thinnest 0.13 mm at (24.3, 10.7, 0.1) in 4 region(s); no region is a wall, 4 taper(s) at feature edges (0.00% of surface, budget 2%); 2 more within measurement error of the limit |
| thickness distribution | PASS | median 2.80 mm, p95 13.27 mm, max 63.53 mm |
| hollowable at 1.20 mm wall | WARN | 0.23 of 2.22 cm3 (10%) in 1 pocket(s) |
| filament that would save | PASS | 0.03 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (73.3, 51.9, 1.0) | 2 | 0.0 | 0.3 | 0.10 |
| 2 | taper | 0.73 mm | (80.7, 39.4, 0.9) | 1 | 0.0 | 0.0 | 0.13 |
| 3 | taper | 0.13 mm | (24.3, 10.7, 0.1) | 12 | 0.0 | 0.2 | 0.02 |
| 4 | taper | 0.53 mm | (21.4, 15.7, 0.1) | 1 | 0.0 | 0.0 | 0.00 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
