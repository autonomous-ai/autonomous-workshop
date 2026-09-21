# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_world_mercury_anti.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0002/thickness-world_mercury_anti.md`

part_world_mercury_anti.step.py: 5.62 cm3 solid, grid 0.133 mm (259x260x131), 150722 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.1% of surface below (151 of 150722 samples); thinnest 0.13 mm at (-5.4, 16.1, 0.0) in 41 region(s); no region is a wall, 40 taper(s) at feature edges and 1 spot(s) too small to be a wall (0.12% of surface, budget 2%); 68 more within measurement error of the limit |
| thickness distribution | PASS | median 4.93 mm, p95 33.53 mm, max 33.87 mm |
| hollowable at 1.20 mm wall | WARN | 2.71 of 5.62 cm3 (48%) in 1 pocket(s) |
| filament that would save | PASS | 0.41 cm3, 0.5 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (15.3, 7.3, 0.0) | 14 | 0.3 | 1.9 | 0.15 |
| 2 | taper | 0.13 mm | (-16.4, 4.1, 0.0) | 11 | 0.2 | 2.1 | 0.09 |
| 3 | taper | 0.13 mm | (6.8, 15.4, 0.0) | 7 | 0.2 | 1.8 | 0.10 |
| 4 | taper | 0.20 mm | (-11.2, -12.8, 0.1) | 6 | 0.2 | 0.9 | 0.19 |
| 5 | taper | 0.13 mm | (-14.4, -8.8, 0.0) | 6 | 0.2 | 2.4 | 0.06 |
| 6 | taper | 0.13 mm | (16.8, 1.9, 0.0) | 7 | 0.1 | 1.3 | 0.11 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
