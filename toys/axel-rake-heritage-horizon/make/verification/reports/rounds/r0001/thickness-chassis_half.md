# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/heritage/part_chassis_half.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/heritage/measure/rounds/r0001/thickness-chassis_half.md`

part_chassis_half.step.py: 31.23 cm3 solid, grid 0.239 mm (603x250x74), 174371 surface samples, thickness resolved to 0.120 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.12) | PASS | 0.0% of surface below (13 of 174371 samples); thinnest 0.24 mm at (1.5, -50.0, 0.1) in 5 region(s); no region is a wall, 5 taper(s) at feature edges (0.01% of surface, budget 2%); 39 more within measurement error of the limit |
| thickness distribution | PASS | median 12.93 mm, p95 47.05 mm, max 69.44 mm |
| hollowable at 1.20 mm wall | WARN | 19.84 of 31.23 cm3 (64%) in 1 pocket(s) |
| filament that would save | PASS | 2.98 cm3, 3.7 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.24 mm | (20.8, -45.8, 14.9) | 6 | 0.4 | 1.4 | 0.32 |
| 2 | taper | 0.24 mm | (-19.9, -45.8, 14.3) | 3 | 0.2 | 1.6 | 0.14 |
| 3 | taper | 0.48 mm | (-1.5, -51.5, 0.1) | 2 | 0.1 | 1.0 | 0.15 |
| 4 | taper | 0.24 mm | (1.5, -50.0, 0.1) | 1 | 0.1 | 0.0 | 0.23 |
| 5 | taper | 0.24 mm | (19.5, -51.5, 0.1) | 1 | 0.0 | 0.0 | 0.15 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
