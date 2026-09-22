# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_05_rear.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/body_05_rear/r0002/thickness-body_05_rear.md`

part_body_05_rear.step.py: 2.86 cm3 solid, grid 0.133 mm (276x232x59), 127045 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.7% of surface below (810 of 127045 samples); thinnest 0.13 mm at (3.1, -9.3, 3.9) in 23 region(s); no region is a wall, 22 taper(s) at feature edges and 1 spot(s) too small to be a wall (0.69% of surface, budget 2%); 79 more within measurement error of the limit |
| thickness distribution | PASS | median 3.47 mm, p95 18.73 mm, max 36.20 mm |
| hollowable at 1.20 mm wall | WARN | 0.53 of 2.86 cm3 (19%) in 1 pocket(s) |
| filament that would save | PASS | 0.08 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (2.5, -9.2, 7.1) | 180 | 3.7 | 5.1 | 0.72 |
| 2 | taper | 0.13 mm | (-3.0, -3.6, 7.1) | 188 | 3.6 | 5.2 | 0.69 |
| 3 | taper | 0.13 mm | (3.2, -3.9, 7.1) | 195 | 3.6 | 5.1 | 0.70 |
| 4 | taper | 0.13 mm | (-3.5, -8.0, 7.1) | 166 | 3.3 | 5.2 | 0.63 |
| 5 | spot | 0.33 mm | (0.0, -13.8, 2.7) | 46 | 1.4 | 1.4 | 1.02 |
| 6 | taper | 0.73 mm | (-6.5, -5.6, 3.5) | 5 | 0.1 | 0.6 | 0.15 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
