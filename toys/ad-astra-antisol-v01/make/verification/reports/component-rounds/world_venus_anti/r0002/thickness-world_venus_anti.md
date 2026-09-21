# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_world_venus_anti.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/world_venus_anti/r0002/thickness-world_venus_anti.md`

part_world_venus_anti.step.py: 6.60 cm3 solid, grid 0.133 mm (259x260x151), 161567 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.1% of surface below (163 of 161567 samples); thinnest 0.13 mm at (-5.3, -16.1, 0.0) in 42 region(s); no region is a wall, 42 taper(s) at feature edges (0.12% of surface, budget 2%); 64 more within measurement error of the limit |
| thickness distribution | PASS | median 4.93 mm, p95 33.53 mm, max 33.87 mm |
| hollowable at 1.20 mm wall | WARN | 3.46 of 6.60 cm3 (52%) in 1 pocket(s) |
| filament that would save | PASS | 0.52 cm3, 0.6 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (-11.5, 12.4, 0.0) | 9 | 0.2 | 2.9 | 0.09 |
| 2 | taper | 0.27 mm | (-4.6, 16.3, 0.0) | 6 | 0.2 | 0.5 | 0.38 |
| 3 | taper | 0.13 mm | (-16.2, -5.0, 0.0) | 10 | 0.2 | 2.6 | 0.07 |
| 4 | taper | 0.13 mm | (-16.8, 1.7, 0.0) | 10 | 0.2 | 1.5 | 0.12 |
| 5 | taper | 0.27 mm | (2.0, 16.8, 0.0) | 5 | 0.2 | 0.7 | 0.25 |
| 6 | taper | 0.13 mm | (-14.8, 8.2, 0.0) | 8 | 0.2 | 2.4 | 0.07 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
