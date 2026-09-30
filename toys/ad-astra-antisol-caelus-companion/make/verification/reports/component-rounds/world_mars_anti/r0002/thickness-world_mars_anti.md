# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_world_mars_anti.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/world_mars_anti/r0002/thickness-world_mars_anti.md`

part_world_mars_anti.step.py: 5.91 cm3 solid, grid 0.133 mm (259x260x138), 154024 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.1% of surface below (167 of 154024 samples); thinnest 0.13 mm at (-2.1, 16.9, 0.0) in 36 region(s); no region is a wall, 36 taper(s) at feature edges (0.13% of surface, budget 2%); 71 more within measurement error of the limit |
| thickness distribution | PASS | median 4.93 mm, p95 33.53 mm, max 33.87 mm |
| hollowable at 1.20 mm wall | WARN | 2.93 of 5.91 cm3 (50%) in 1 pocket(s) |
| filament that would save | PASS | 0.44 cm3, 0.5 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (14.4, 8.8, 0.0) | 11 | 0.2 | 3.4 | 0.07 |
| 2 | taper | 0.13 mm | (14.6, -8.6, 0.0) | 9 | 0.2 | 2.8 | 0.07 |
| 3 | taper | 0.13 mm | (-15.3, -7.1, 0.0) | 11 | 0.2 | 4.1 | 0.05 |
| 4 | taper | 0.13 mm | (-1.6, -16.8, 0.0) | 7 | 0.2 | 1.6 | 0.12 |
| 5 | taper | 0.13 mm | (9.1, 14.3, 0.0) | 10 | 0.2 | 3.6 | 0.05 |
| 6 | taper | 0.40 mm | (-8.1, -14.9, 0.0) | 10 | 0.2 | 1.4 | 0.12 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
