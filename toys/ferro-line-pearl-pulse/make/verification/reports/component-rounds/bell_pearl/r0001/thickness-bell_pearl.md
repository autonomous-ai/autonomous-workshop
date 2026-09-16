# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_bell_pearl.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/bell_pearl/r0001/thickness-bell_pearl.md`

part_bell_pearl.step.py: 7.97 cm3 solid, grid 0.228 mm (364x364x84), 253895 surface samples, thickness resolved to 0.114 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.11) | FAIL | 1.4% of surface below (3149 of 253895 samples); thinnest 0.23 mm at (-40.7, 1.8, 17.9) in 13 region(s); 2 wall(s) (widest band 6.30 mm), 11 taper(s) at feature edges (0.04% of surface, budget 2%); 1326 more within measurement error of the limit |
| thickness distribution | PASS | median 1.14 mm, p95 1.71 mm, max 42.87 mm |
| hollowable at 1.20 mm wall | PASS | 0.00 of 7.97 cm3 (0%) in 0 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.23 mm | (-40.7, 1.8, 17.9) | 2483 | 157.1 | 115.4 | 1.36 |
| 2 | wall | 0.23 mm | (4.4, 22.4, 3.1) | 596 | 36.3 | 5.8 | 6.30 |
| 3 | taper | 0.34 mm | (21.8, 32.4, 18.0) | 42 | 2.9 | 6.6 | 0.45 |
| 4 | taper | 0.34 mm | (11.6, 24.9, 0.9) | 9 | 0.7 | 2.4 | 0.29 |
| 5 | taper | 0.23 mm | (15.5, 22.3, 2.2) | 10 | 0.6 | 4.2 | 0.14 |
| 6 | taper | 0.68 mm | (23.7, 20.3, 5.7) | 2 | 0.1 | 0.7 | 0.20 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
