# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/heritage/part_chassis_half.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/heritage/measure/component-rounds/chassis_half/r0001/thickness-chassis_half.md`

part_chassis_half.step.py: 31.12 cm3 solid, grid 0.239 mm (603x245x74), 173583 surface samples, thickness resolved to 0.120 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.12) | PASS | 0.0% of surface below (20 of 173583 samples); thinnest 0.24 mm at (16.5, -49.5, 0.1) in 4 region(s); no region is a wall, 4 taper(s) at feature edges (0.01% of surface, budget 2%); 1433 more within measurement error of the limit |
| thickness distribution | PASS | median 12.93 mm, p95 47.05 mm, max 69.44 mm |
| hollowable at 1.20 mm wall | WARN | 19.84 of 31.12 cm3 (64%) in 1 pocket(s) |
| filament that would save | PASS | 2.98 cm3, 3.7 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.48 mm | (20.7, -46.1, 14.1) | 10 | 0.7 | 1.6 | 0.46 |
| 2 | taper | 0.24 mm | (-19.8, -45.8, 13.7) | 6 | 0.4 | 1.6 | 0.29 |
| 3 | taper | 0.24 mm | (16.5, -49.5, 0.1) | 3 | 0.2 | 0.3 | 0.66 |
| 4 | taper | 0.48 mm | (-1.5, -51.7, 0.1) | 1 | 0.1 | 0.0 | 0.31 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
