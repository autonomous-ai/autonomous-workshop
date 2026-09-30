# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_world_jupiter_anti.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/world_jupiter_anti/r0002/thickness-world_jupiter_anti.md`

part_world_jupiter_anti.step.py: 14.65 cm3 solid, grid 0.147 mm (236x236x209), 184114 surface samples, thickness resolved to 0.074 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.1% of surface below (129 of 184114 samples); thinnest 0.15 mm at (-2.1, 16.9, 0.1) in 34 region(s); no region is a wall, 34 taper(s) at feature edges (0.08% of surface, budget 2%); 53 more within measurement error of the limit |
| thickness distribution | PASS | median 26.83 mm, p95 33.59 mm, max 35.87 mm |
| hollowable at 1.20 mm wall | WARN | 10.19 of 14.65 cm3 (70%) in 1 pocket(s) |
| filament that would save | PASS | 1.53 cm3, 1.9 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.15 mm | (-10.3, 13.4, 0.0) | 13 | 0.3 | 4.0 | 0.08 |
| 2 | taper | 0.15 mm | (-5.7, -16.0, 0.0) | 15 | 0.3 | 4.2 | 0.08 |
| 3 | taper | 0.15 mm | (7.4, -15.3, 0.0) | 7 | 0.2 | 2.6 | 0.09 |
| 4 | taper | 0.15 mm | (-12.7, 11.2, 0.0) | 8 | 0.2 | 2.0 | 0.09 |
| 5 | taper | 0.29 mm | (-10.9, -12.9, 0.0) | 5 | 0.2 | 0.4 | 0.42 |
| 6 | taper | 0.15 mm | (4.6, -16.4, 0.0) | 7 | 0.2 | 1.0 | 0.16 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
