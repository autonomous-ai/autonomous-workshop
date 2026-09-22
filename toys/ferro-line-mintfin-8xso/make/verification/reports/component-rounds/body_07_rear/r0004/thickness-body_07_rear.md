# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_07_rear.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/body_07_rear/r0004/thickness-body_07_rear.md`

part_body_07_rear.step.py: 0.91 cm3 solid, grid 0.133 mm (150x132x57), 53064 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.3% of surface below (162 of 53064 samples); thinnest 0.13 mm at (-7.6, -1.5, 3.1) in 24 region(s); no region is a wall, 24 taper(s) at feature edges (0.33% of surface, budget 2%); 30 more within measurement error of the limit |
| thickness distribution | PASS | median 3.40 mm, p95 6.93 mm, max 9.87 mm |
| hollowable at 1.20 mm wall | WARN | 0.07 of 0.91 cm3 (8%) in 3 pocket(s) |
| filament that would save | PASS | 0.01 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (7.6, -1.7, 3.1) | 45 | 1.0 | 2.1 | 0.48 |
| 2 | taper | 0.13 mm | (-7.6, -1.5, 3.1) | 41 | 0.9 | 2.2 | 0.41 |
| 3 | taper | 0.53 mm | (-6.6, -1.2, 6.8) | 14 | 0.3 | 3.3 | 0.09 |
| 4 | taper | 0.20 mm | (3.9, -1.2, 1.5) | 9 | 0.1 | 0.7 | 0.20 |
| 5 | taper | 0.60 mm | (3.8, -3.0, 6.9) | 7 | 0.1 | 1.8 | 0.08 |
| 6 | taper | 0.40 mm | (0.5, -8.4, 6.6) | 5 | 0.1 | 0.4 | 0.23 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
