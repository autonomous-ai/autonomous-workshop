# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_world_saturn_sol.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/world_saturn_sol/r0006/thickness-world_saturn_sol.md`

part_world_saturn_sol.step.py: 14.64 cm3 solid, grid 0.147 mm (235x235x202), 193406 surface samples, thickness resolved to 0.074 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (3 of 193406 samples); thinnest 0.29 mm at (-13.1, 5.5, 23.5) in 3 region(s); no region is a wall, 3 taper(s) at feature edges (0.00% of surface, budget 2%); 1 more within measurement error of the limit |
| thickness distribution | PASS | median 25.87 mm, p95 33.44 mm, max 35.79 mm |
| hollowable at 1.20 mm wall | WARN | 9.85 of 14.64 cm3 (67%) in 1 pocket(s), 1 too small to shell |
| filament that would save | PASS | 1.48 cm3, 1.8 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.29 mm | (-13.1, 5.5, 23.5) | 1 | 0.0 | 0.0 | 0.18 |
| 2 | taper | 0.44 mm | (6.9, -14.2, 13.4) | 1 | 0.0 | 0.0 | 0.17 |
| 3 | taper | 0.44 mm | (-5.5, -14.6, 19.6) | 1 | 0.0 | 0.0 | 0.17 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
