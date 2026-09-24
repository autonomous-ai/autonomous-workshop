# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_world_mercury_anti.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/world_mercury_anti/r0001/thickness-world_mercury_anti.md`

part_world_mercury_anti.step.py: 5.62 cm3 solid, grid 0.133 mm (259x260x131), 150714 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.1% of surface below (155 of 150714 samples); thinnest 0.13 mm at (-5.4, 16.1, 0.0) in 44 region(s); no region is a wall, 44 taper(s) at feature edges (0.13% of surface, budget 2%); 63 more within measurement error of the limit |
| thickness distribution | PASS | median 4.93 mm, p95 33.53 mm, max 33.87 mm |
| hollowable at 1.20 mm wall | WARN | 2.71 of 5.62 cm3 (48%) in 1 pocket(s) |
| filament that would save | PASS | 0.41 cm3, 0.5 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.27 mm | (2.0, 16.8, 0.0) | 7 | 0.3 | 1.3 | 0.24 |
| 2 | taper | 0.13 mm | (9.5, 14.0, 0.0) | 16 | 0.3 | 4.5 | 0.06 |
| 3 | taper | 0.27 mm | (-1.3, -16.9, 0.0) | 7 | 0.2 | 0.7 | 0.24 |
| 4 | taper | 0.20 mm | (-11.2, -12.8, 0.1) | 6 | 0.2 | 0.9 | 0.19 |
| 5 | taper | 0.27 mm | (3.9, -16.5, 0.0) | 8 | 0.2 | 1.0 | 0.15 |
| 6 | taper | 0.40 mm | (-14.6, 8.5, 0.0) | 7 | 0.1 | 1.0 | 0.14 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
