# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/heritage/part_chassis_half.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/heritage/measure/component-rounds/chassis_half/r0006/thickness-chassis_half.md`

part_chassis_half.step.py: 30.35 cm3 solid, grid 0.239 mm (603x250x74), 171725 surface samples, thickness resolved to 0.120 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.12) | PASS | 0.0% of surface below (27 of 171725 samples); thinnest 0.24 mm at (20.8, -45.8, 15.1) in 4 region(s); no region is a wall, 4 taper(s) at feature edges (0.02% of surface, budget 2%); 25 more within measurement error of the limit |
| thickness distribution | PASS | median 12.93 mm, p95 47.05 mm, max 67.64 mm |
| hollowable at 1.20 mm wall | WARN | 19.20 of 30.35 cm3 (63%) in 2 pocket(s), 1 too small to shell |
| filament that would save | PASS | 2.88 cm3, 3.6 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.24 mm | (20.8, -45.8, 15.1) | 13 | 1.0 | 1.9 | 0.52 |
| 2 | taper | 0.24 mm | (-19.9, -45.8, 13.7) | 11 | 0.8 | 2.0 | 0.40 |
| 3 | taper | 0.60 mm | (16.5, -51.4, 0.1) | 2 | 0.2 | 0.6 | 0.29 |
| 4 | taper | 0.24 mm | (1.5, -50.0, 0.1) | 1 | 0.1 | 0.0 | 0.31 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
