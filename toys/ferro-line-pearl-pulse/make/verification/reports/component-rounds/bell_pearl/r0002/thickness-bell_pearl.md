# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_bell_pearl.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/bell_pearl/r0002/thickness-bell_pearl.md`

part_bell_pearl.step.py: 8.37 cm3 solid, grid 0.228 mm (364x364x84), 257828 surface samples, thickness resolved to 0.114 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.11) | FAIL | 5.9% of surface below (15137 of 257828 samples); thinnest 0.23 mm at (-32.1, -22.9, 17.9) in 18 region(s); 4 wall(s) (widest band 6.84 mm), 13 taper(s) at feature edges and 1 spot(s) too small to be a wall (0.04% of surface, budget 2%); 13078 more within measurement error of the limit |
| thickness distribution | PASS | median 1.14 mm, p95 2.85 mm, max 42.76 mm |
| hollowable at 1.20 mm wall | PASS | 0.00 of 8.37 cm3 (0%) in 0 pocket(s), 33 too small to shell |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.34 mm | (-8.4, -27.4, 2.2) | 11336 | 600.5 | 87.8 | 6.84 |
| 2 | wall | 0.23 mm | (-32.1, -22.9, 17.9) | 2565 | 151.3 | 115.5 | 1.31 |
| 3 | wall | 0.23 mm | (4.4, 22.4, 5.8) | 596 | 36.2 | 7.2 | 5.05 |
| 4 | wall | 0.23 mm | (16.5, 23.6, 3.8) | 550 | 30.3 | 8.4 | 3.59 |
| 5 | taper | 0.23 mm | (16.9, 36.3, 17.2) | 72 | 4.4 | 8.9 | 0.49 |
| 6 | spot | 0.68 mm | (18.0, 25.7, 8.5) | 1 | 0.2 | 0.0 | 0.93 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
