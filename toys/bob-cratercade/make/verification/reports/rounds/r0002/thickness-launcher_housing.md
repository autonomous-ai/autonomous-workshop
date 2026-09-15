# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_launcher_housing.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0002/thickness-launcher_housing.md`

part_launcher_housing.step.py: 37.00 cm3 solid, grid 0.264 mm (194x687x82), 322652 surface samples, thickness resolved to 0.132 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.13) | FAIL | 0.1% of surface below (151 of 322652 samples); thinnest 0.26 mm at (5.8, 35.9, 11.7) in 6 region(s); 3 wall(s) (widest band 1.81 mm), 3 taper(s) at feature edges (0.02% of surface, budget 2%); 427 more within measurement error of the limit |
| thickness distribution | PASS | median 3.04 mm, p95 23.89 mm, max 180.04 mm |
| hollowable at 1.20 mm wall | WARN | 8.40 of 37.00 cm3 (23%) in 1 pocket(s) |
| filament that would save | PASS | 1.26 cm3, 1.6 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.26 mm | (32.6, 16.0, 4.7) | 37 | 3.8 | 2.1 | 1.81 |
| 2 | wall | 0.26 mm | (32.6, 35.8, 4.3) | 34 | 3.7 | 3.1 | 1.18 |
| 3 | wall | 0.40 mm | (5.9, 28.0, 12.8) | 24 | 1.9 | 2.2 | 0.88 |
| 4 | taper | 0.26 mm | (12.4, 153.0, 11.1) | 20 | 1.6 | 2.1 | 0.77 |
| 5 | taper | 0.26 mm | (12.2, 160.8, 11.4) | 18 | 1.5 | 2.0 | 0.76 |
| 6 | taper | 0.26 mm | (5.8, 35.9, 11.7) | 18 | 1.4 | 2.2 | 0.64 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
