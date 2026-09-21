# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_lane_19_yellow.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/lane_19_yellow/r0001/thickness-lane_19_yellow.md`

part_lane_19_yellow.step.py: 2.16 cm3 solid, grid 0.133 mm (487x226x35), 114532 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (16 of 114532 samples); thinnest 0.13 mm at (-24.8, 9.3, 1.8) in 4 region(s); no region is a wall, 4 taper(s) at feature edges (0.00% of surface, budget 2%); 1 more within measurement error of the limit |
| thickness distribution | PASS | median 2.80 mm, p95 13.20 mm, max 63.53 mm |
| hollowable at 1.20 mm wall | WARN | 0.22 of 2.16 cm3 (10%) in 1 pocket(s) |
| filament that would save | PASS | 0.03 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (-24.8, 9.3, 1.8) | 2 | 0.0 | 0.0 | 0.27 |
| 2 | taper | 0.47 mm | (-88.7, 13.8, 1.0) | 1 | 0.0 | 0.0 | 0.14 |
| 3 | taper | 0.60 mm | (-88.3, 16.1, 1.0) | 1 | 0.0 | 0.0 | 0.14 |
| 4 | taper | 0.13 mm | (-24.8, 9.6, 0.0) | 12 | 0.0 | 0.2 | 0.02 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
