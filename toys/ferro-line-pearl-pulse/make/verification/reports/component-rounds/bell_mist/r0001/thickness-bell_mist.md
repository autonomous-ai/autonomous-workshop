# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_bell_mist.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/bell_mist/r0001/thickness-bell_mist.md`

part_bell_mist.step.py: 0.28 cm3 solid, grid 0.133 mm (170x173x140), 29683 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | FAIL | 1.9% of surface below (553 of 29683 samples); thinnest 0.13 mm at (18.6, 26.5, 9.6) in 3 region(s); 1 wall(s) (widest band 0.97 mm), 2 taper(s) at feature edges (0.03% of surface, budget 2%); 29 more within measurement error of the limit |
| thickness distribution | PASS | median 1.13 mm, p95 6.33 mm, max 12.80 mm |
| hollowable at 1.20 mm wall | PASS | 0.00 of 0.28 cm3 (0%) in 0 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.13 mm | (21.7, 31.0, 17.8) | 544 | 10.9 | 11.3 | 0.97 |
| 2 | taper | 0.27 mm | (20.9, 18.2, 1.0) | 7 | 0.1 | 1.6 | 0.09 |
| 3 | taper | 0.13 mm | (18.6, 26.5, 9.6) | 2 | 0.0 | 1.2 | 0.03 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
