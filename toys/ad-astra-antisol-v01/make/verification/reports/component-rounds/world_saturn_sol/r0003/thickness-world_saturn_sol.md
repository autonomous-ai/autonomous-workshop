# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_world_saturn_sol.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/world_saturn_sol/r0003/thickness-world_saturn_sol.md`

part_world_saturn_sol.step.py: 14.69 cm3 solid, grid 0.147 mm (235x235x202), 191125 surface samples, thickness resolved to 0.074 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.2% of surface below (157 of 191125 samples); thinnest 0.15 mm at (7.7, 12.8, 10.3) in 61 region(s); no region is a wall, 57 taper(s) at feature edges and 4 spot(s) too small to be a wall (0.20% of surface, budget 2%); 15 more within measurement error of the limit |
| thickness distribution | PASS | median 25.87 mm, p95 33.44 mm, max 35.79 mm |
| hollowable at 1.20 mm wall | WARN | 9.87 of 14.69 cm3 (67%) in 1 pocket(s), 6 too small to shell |
| filament that would save | PASS | 1.48 cm3, 1.8 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.15 mm | (7.7, 12.8, 10.3) | 8 | 0.7 | 2.1 | 0.36 |
| 2 | spot | 0.15 mm | (8.6, -11.9, 9.7) | 2 | 0.7 | 0.4 | 1.97 |
| 3 | spot | 0.15 mm | (7.7, -12.9, 10.4) | 4 | 0.5 | 0.2 | 2.75 |
| 4 | taper | 0.22 mm | (5.4, -13.8, 10.9) | 4 | 0.4 | 0.9 | 0.51 |
| 5 | taper | 0.44 mm | (5.5, 14.0, 11.2) | 2 | 0.4 | 0.6 | 0.72 |
| 6 | taper | 0.22 mm | (7.2, -12.0, 9.3) | 3 | 0.4 | 1.4 | 0.30 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
