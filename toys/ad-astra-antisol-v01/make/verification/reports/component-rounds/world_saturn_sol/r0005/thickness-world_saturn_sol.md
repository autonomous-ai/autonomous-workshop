# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_world_saturn_sol.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/world_saturn_sol/r0005/thickness-world_saturn_sol.md`

part_world_saturn_sol.step.py: 14.55 cm3 solid, grid 0.147 mm (235x235x202), 194610 surface samples, thickness resolved to 0.074 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (4 of 194610 samples); thinnest 0.15 mm at (-12.5, -6.9, 23.2) in 4 region(s); no region is a wall, 4 taper(s) at feature edges (0.00% of surface, budget 2%) |
| thickness distribution | PASS | median 25.87 mm, p95 33.44 mm, max 35.21 mm |
| hollowable at 1.20 mm wall | WARN | 9.77 of 14.55 cm3 (67%) in 1 pocket(s) |
| filament that would save | PASS | 1.47 cm3, 1.8 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.29 mm | (-11.0, 9.6, 22.4) | 1 | 0.0 | 0.0 | 0.17 |
| 2 | taper | 0.29 mm | (-11.8, 8.4, 22.8) | 1 | 0.0 | 0.0 | 0.17 |
| 3 | taper | 0.15 mm | (-12.5, -6.9, 23.2) | 1 | 0.0 | 0.0 | 0.15 |
| 4 | taper | 0.44 mm | (-4.2, -15.2, 19.0) | 1 | 0.0 | 0.0 | 0.14 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
