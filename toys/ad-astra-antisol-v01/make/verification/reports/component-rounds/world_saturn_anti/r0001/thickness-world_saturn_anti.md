# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_world_saturn_anti.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/world_saturn_anti/r0001/thickness-world_saturn_anti.md`

part_world_saturn_anti.step.py: 14.00 cm3 solid, grid 0.147 mm (236x236x202), 200745 surface samples, thickness resolved to 0.074 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.1% of surface below (113 of 200745 samples); thinnest 0.15 mm at (-8.5, -14.7, 0.0) in 48 region(s); no region is a wall, 48 taper(s) at feature edges (0.07% of surface, budget 2%); 57 more within measurement error of the limit |
| thickness distribution | PASS | median 25.80 mm, p95 33.52 mm, max 34.62 mm |
| hollowable at 1.20 mm wall | WARN | 9.27 of 14.00 cm3 (66%) in 1 pocket(s) |
| filament that would save | PASS | 1.39 cm3, 1.7 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.15 mm | (-16.1, -5.2, 0.0) | 8 | 0.2 | 2.9 | 0.06 |
| 2 | taper | 0.15 mm | (5.6, -15.9, 0.0) | 7 | 0.2 | 2.4 | 0.07 |
| 3 | taper | 0.15 mm | (-7.3, 15.3, 0.0) | 7 | 0.2 | 2.2 | 0.07 |
| 4 | taper | 0.44 mm | (8.8, 14.4, 0.0) | 2 | 0.1 | 0.2 | 0.58 |
| 5 | taper | 0.15 mm | (1.2, 16.9, 0.0) | 4 | 0.1 | 1.0 | 0.14 |
| 6 | taper | 0.15 mm | (-8.5, -14.7, 0.0) | 6 | 0.1 | 2.0 | 0.06 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
