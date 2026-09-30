# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_world_saturn_sol.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0002/thickness-world_saturn_sol.md`

part_world_saturn_sol.step.py: 14.14 cm3 solid, grid 0.147 mm (235x235x202), 186658 surface samples, thickness resolved to 0.074 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (21 of 186658 samples); thinnest 0.15 mm at (-11.1, -7.9, 22.3) in 16 region(s); no region is a wall, 15 taper(s) at feature edges and 1 spot(s) too small to be a wall (0.03% of surface, budget 2%) |
| thickness distribution | PASS | median 25.87 mm, p95 33.44 mm, max 34.62 mm |
| hollowable at 1.20 mm wall | WARN | 9.54 of 14.14 cm3 (67%) in 1 pocket(s) |
| filament that would save | PASS | 1.43 cm3, 1.8 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.15 mm | (-13.6, 0.7, 22.5) | 2 | 0.3 | 0.6 | 0.46 |
| 2 | taper | 0.15 mm | (-13.1, -3.9, 22.3) | 2 | 0.2 | 0.3 | 0.74 |
| 3 | taper | 0.15 mm | (-12.7, -5.7, 22.1) | 2 | 0.2 | 0.6 | 0.26 |
| 4 | spot | 0.15 mm | (-11.9, 7.4, 21.7) | 1 | 0.1 | 0.0 | 0.95 |
| 5 | taper | 0.15 mm | (-13.5, -0.7, 22.5) | 1 | 0.1 | 0.0 | 0.66 |
| 6 | taper | 0.15 mm | (-12.2, -6.5, 21.8) | 1 | 0.1 | 0.0 | 0.63 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
