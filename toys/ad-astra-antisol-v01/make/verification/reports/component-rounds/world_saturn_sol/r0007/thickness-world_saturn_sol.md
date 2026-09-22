# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_world_saturn_sol.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/world_saturn_sol/r0007/thickness-world_saturn_sol.md`

part_world_saturn_sol.step.py: 14.14 cm3 solid, grid 0.147 mm (235x235x202), 186495 surface samples, thickness resolved to 0.074 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (11 of 186495 samples); thinnest 0.15 mm at (-12.3, -5.2, 22.9) in 11 region(s); no region is a wall, 11 taper(s) at feature edges (0.01% of surface, budget 2%) |
| thickness distribution | PASS | median 25.87 mm, p95 33.44 mm, max 34.62 mm |
| hollowable at 1.20 mm wall | WARN | 9.54 of 14.14 cm3 (67%) in 1 pocket(s) |
| filament that would save | PASS | 1.43 cm3, 1.8 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.51 mm | (-7.5, -12.2, 20.5) | 1 | 0.0 | 0.0 | 0.22 |
| 2 | taper | 0.22 mm | (6.4, -13.3, 13.5) | 1 | 0.0 | 0.0 | 0.21 |
| 3 | taper | 0.15 mm | (-12.3, -5.2, 22.9) | 1 | 0.0 | 0.0 | 0.20 |
| 4 | taper | 0.22 mm | (7.5, -12.6, 12.9) | 1 | 0.0 | 0.0 | 0.19 |
| 5 | taper | 0.22 mm | (-12.7, 3.7, 23.1) | 1 | 0.0 | 0.0 | 0.18 |
| 6 | taper | 0.44 mm | (5.2, 14.0, 14.1) | 1 | 0.0 | 0.0 | 0.18 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
