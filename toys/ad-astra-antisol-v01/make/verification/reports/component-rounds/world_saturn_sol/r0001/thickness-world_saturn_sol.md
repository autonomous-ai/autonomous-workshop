# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_world_saturn_sol.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/world_saturn_sol/r0001/thickness-world_saturn_sol.md`

part_world_saturn_sol.step.py: 14.01 cm3 solid, grid 0.147 mm (235x235x202), 200137 surface samples, thickness resolved to 0.074 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (5 of 200137 samples); thinnest 0.15 mm at (-13.5, -3.9, 23.7) in 5 region(s); no region is a wall, 5 taper(s) at feature edges (0.00% of surface, budget 2%) |
| thickness distribution | PASS | median 25.87 mm, p95 33.44 mm, max 34.62 mm |
| hollowable at 1.20 mm wall | WARN | 9.27 of 14.01 cm3 (66%) in 1 pocket(s) |
| filament that would save | PASS | 1.39 cm3, 1.7 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.44 mm | (-4.2, -15.2, 19.0) | 1 | 0.0 | 0.0 | 0.18 |
| 2 | taper | 0.22 mm | (-14.6, 0.8, 22.5) | 1 | 0.0 | 0.0 | 0.18 |
| 3 | taper | 0.29 mm | (11.4, 9.0, 9.4) | 1 | 0.0 | 0.0 | 0.16 |
| 4 | taper | 0.15 mm | (-13.5, -3.9, 23.7) | 1 | 0.0 | 0.0 | 0.16 |
| 5 | taper | 0.29 mm | (-9.0, 12.0, 21.4) | 1 | 0.0 | 0.0 | 0.16 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
