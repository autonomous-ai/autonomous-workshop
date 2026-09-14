# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/heritage/part_chassis_half_right.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/heritage/measure/rounds/r0001/thickness-chassis_half_right.md`

part_chassis_half_right.step.py: 31.24 cm3 solid, grid 0.239 mm (603x250x74), 174396 surface samples, thickness resolved to 0.120 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.12) | PASS | 0.0% of surface below (34 of 174396 samples); thinnest 0.24 mm at (1.5, 50.1, 0.1) in 7 region(s); no region is a wall, 7 taper(s) at feature edges (0.02% of surface, budget 2%); 21 more within measurement error of the limit |
| thickness distribution | PASS | median 12.93 mm, p95 47.05 mm, max 69.68 mm |
| hollowable at 1.20 mm wall | WARN | 19.85 of 31.24 cm3 (64%) in 1 pocket(s) |
| filament that would save | PASS | 2.98 cm3, 3.7 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.36 mm | (20.7, 46.1, 15.0) | 21 | 1.6 | 2.1 | 0.77 |
| 2 | taper | 0.36 mm | (-19.7, 46.1, 15.0) | 8 | 0.6 | 2.0 | 0.31 |
| 3 | taper | 0.60 mm | (16.5, 50.4, 0.1) | 1 | 0.1 | 0.0 | 0.31 |
| 4 | taper | 0.48 mm | (-1.5, 51.1, 0.1) | 1 | 0.1 | 0.0 | 0.31 |
| 5 | taper | 0.60 mm | (16.5, 51.7, 0.1) | 1 | 0.1 | 0.0 | 0.23 |
| 6 | taper | 0.24 mm | (1.5, 50.1, 0.1) | 1 | 0.1 | 0.0 | 0.23 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
