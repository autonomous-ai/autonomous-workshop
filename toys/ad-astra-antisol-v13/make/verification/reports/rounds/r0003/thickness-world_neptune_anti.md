# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_world_neptune_anti.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0003/thickness-world_neptune_anti.md`

part_world_neptune_anti.step.py: 9.81 cm3 solid, grid 0.140 mm (247x248x183), 172016 surface samples, thickness resolved to 0.070 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.1% of surface below (152 of 172016 samples); thinnest 0.14 mm at (-16.5, 4.2, 0.1) in 32 region(s); no region is a wall, 32 taper(s) at feature edges (0.11% of surface, budget 2%); 2 more within measurement error of the limit |
| thickness distribution | PASS | median 21.70 mm, p95 33.46 mm, max 33.81 mm |
| hollowable at 1.20 mm wall | WARN | 6.00 of 9.81 cm3 (61%) in 1 pocket(s) |
| filament that would save | PASS | 0.90 cm3, 1.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.28 mm | (-10.4, 13.3, 0.0) | 23 | 0.6 | 6.2 | 0.09 |
| 2 | taper | 0.28 mm | (-15.5, 6.7, 0.0) | 5 | 0.2 | 1.2 | 0.20 |
| 3 | taper | 0.14 mm | (-16.5, 4.2, 0.1) | 12 | 0.2 | 3.4 | 0.07 |
| 4 | taper | 0.14 mm | (-8.6, -14.6, 0.0) | 11 | 0.2 | 1.6 | 0.14 |
| 5 | taper | 0.28 mm | (-6.3, -15.7, 0.0) | 9 | 0.2 | 1.7 | 0.10 |
| 6 | taper | 0.42 mm | (-11.8, -12.1, 0.0) | 8 | 0.2 | 1.0 | 0.17 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
