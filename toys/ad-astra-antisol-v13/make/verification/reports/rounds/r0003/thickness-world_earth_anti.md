# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_world_earth_anti.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0003/thickness-world_earth_anti.md`

part_world_earth_anti.step.py: 6.68 cm3 solid, grid 0.133 mm (259x260x153), 162112 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.1% of surface below (164 of 162112 samples); thinnest 0.13 mm at (13.0, 10.9, 0.0) in 37 region(s); no region is a wall, 37 taper(s) at feature edges (0.13% of surface, budget 2%); 76 more within measurement error of the limit |
| thickness distribution | PASS | median 4.93 mm, p95 33.53 mm, max 33.87 mm |
| hollowable at 1.20 mm wall | WARN | 3.52 of 6.68 cm3 (53%) in 1 pocket(s) |
| filament that would save | PASS | 0.53 cm3, 0.7 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.27 mm | (-16.8, -1.6, 0.0) | 17 | 0.3 | 4.3 | 0.07 |
| 2 | taper | 0.13 mm | (15.4, 7.1, 0.0) | 11 | 0.3 | 2.4 | 0.12 |
| 3 | taper | 0.13 mm | (-2.2, 16.8, 0.0) | 13 | 0.3 | 1.8 | 0.14 |
| 4 | taper | 0.13 mm | (-1.7, -16.8, 0.0) | 6 | 0.2 | 1.6 | 0.14 |
| 5 | taper | 0.13 mm | (-16.4, 4.2, 0.0) | 12 | 0.2 | 2.1 | 0.10 |
| 6 | taper | 0.13 mm | (16.7, -2.8, 0.0) | 7 | 0.2 | 1.2 | 0.13 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
