# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_world_saturn_anti.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/world_saturn_anti/r0003/thickness-world_saturn_anti.md`

part_world_saturn_anti.step.py: 14.69 cm3 solid, grid 0.147 mm (236x236x202), 191695 surface samples, thickness resolved to 0.074 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.3% of surface below (275 of 191695 samples); thinnest 0.15 mm at (-2.1, -16.9, 0.1) in 97 region(s); no region is a wall, 92 taper(s) at feature edges and 5 spot(s) too small to be a wall (0.33% of surface, budget 2%); 56 more within measurement error of the limit |
| thickness distribution | PASS | median 25.80 mm, p95 33.52 mm, max 36.16 mm |
| hollowable at 1.20 mm wall | WARN | 9.87 of 14.69 cm3 (67%) in 1 pocket(s), 7 too small to shell |
| filament that would save | PASS | 1.48 cm3, 1.8 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.15 mm | (-7.9, 13.2, 11.1) | 3 | 1.5 | 2.0 | 0.74 |
| 2 | taper | 0.15 mm | (12.8, -6.5, 20.6) | 14 | 0.8 | 2.5 | 0.32 |
| 3 | taper | 0.15 mm | (12.6, 7.9, 20.7) | 12 | 0.7 | 2.9 | 0.24 |
| 4 | spot | 0.15 mm | (-8.7, -12.0, 9.9) | 1 | 0.7 | 0.0 | 4.68 |
| 5 | taper | 0.15 mm | (-6.6, 13.6, 10.8) | 9 | 0.6 | 2.0 | 0.32 |
| 6 | taper | 0.15 mm | (-5.6, 14.2, 11.3) | 7 | 0.5 | 0.9 | 0.56 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
