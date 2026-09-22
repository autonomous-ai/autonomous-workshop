# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_world_saturn_sol.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/world_saturn_sol/r0002/thickness-world_saturn_sol.md`

part_world_saturn_sol.step.py: 14.67 cm3 solid, grid 0.147 mm (235x235x202), 193583 surface samples, thickness resolved to 0.074 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.1% of surface below (119 of 193583 samples); thinnest 0.15 mm at (1.4, -9.9, 6.7) in 37 region(s); no region is a wall, 36 taper(s) at feature edges and 1 spot(s) too small to be a wall (0.14% of surface, budget 2%); 12 more within measurement error of the limit |
| thickness distribution | PASS | median 25.87 mm, p95 33.44 mm, max 35.87 mm |
| hollowable at 1.20 mm wall | WARN | 9.83 of 14.67 cm3 (67%) in 1 pocket(s), 6 too small to shell |
| filament that would save | PASS | 1.47 cm3, 1.8 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.15 mm | (-10.9, -10.9, 20.8) | 23 | 1.6 | 7.3 | 0.22 |
| 2 | taper | 0.15 mm | (-10.2, 11.7, 20.8) | 25 | 1.6 | 7.7 | 0.20 |
| 3 | spot | 0.44 mm | (11.8, 7.9, 8.6) | 1 | 0.5 | 0.0 | 3.08 |
| 4 | taper | 0.15 mm | (-13.4, -6.4, 22.1) | 4 | 0.3 | 2.6 | 0.14 |
| 5 | taper | 0.15 mm | (-13.7, 5.4, 21.3) | 6 | 0.2 | 0.8 | 0.18 |
| 6 | taper | 0.37 mm | (-9.5, -12.2, 18.7) | 4 | 0.1 | 0.4 | 0.30 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
