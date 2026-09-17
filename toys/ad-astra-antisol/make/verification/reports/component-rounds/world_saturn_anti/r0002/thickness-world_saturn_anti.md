# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_world_saturn_anti.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/world_saturn_anti/r0002/thickness-world_saturn_anti.md`

part_world_saturn_anti.step.py: 14.67 cm3 solid, grid 0.147 mm (236x236x202), 194141 surface samples, thickness resolved to 0.074 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.2% of surface below (237 of 194141 samples); thinnest 0.15 mm at (-17.0, -0.9, 0.0) in 80 region(s); no region is a wall, 76 taper(s) at feature edges and 4 spot(s) too small to be a wall (0.21% of surface, budget 2%); 54 more within measurement error of the limit |
| thickness distribution | PASS | median 25.80 mm, p95 33.52 mm, max 36.09 mm |
| hollowable at 1.20 mm wall | WARN | 9.83 of 14.67 cm3 (67%) in 1 pocket(s), 7 too small to shell |
| filament that would save | PASS | 1.47 cm3, 1.8 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.15 mm | (12.9, -8.1, 20.8) | 18 | 1.1 | 4.4 | 0.24 |
| 2 | taper | 0.15 mm | (13.0, 7.3, 22.1) | 6 | 0.6 | 2.2 | 0.29 |
| 3 | taper | 0.15 mm | (11.2, 10.5, 20.8) | 13 | 0.6 | 2.9 | 0.20 |
| 4 | taper | 0.15 mm | (9.1, 12.9, 20.0) | 6 | 0.4 | 1.9 | 0.20 |
| 5 | spot | 0.15 mm | (-10.1, -9.8, 8.8) | 2 | 0.3 | 0.3 | 1.25 |
| 6 | spot | 0.29 mm | (14.4, 2.8, 21.9) | 3 | 0.3 | 0.3 | 0.88 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
