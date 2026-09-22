# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_02_rear.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/body_02_rear/r0006/thickness-body_02_rear.md`

part_body_02_rear.step.py: 5.91 cm3 solid, grid 0.133 mm (452x334x66), 256888 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.4% of surface below (840 of 256888 samples); thinnest 0.13 mm at (-5.1, -12.9, 0.0) in 23 region(s); no region is a wall, 23 taper(s) at feature edges (0.37% of surface, budget 2%); 186 more within measurement error of the limit |
| thickness distribution | PASS | median 3.13 mm, p95 19.93 mm, max 59.60 mm |
| hollowable at 1.20 mm wall | WARN | 0.98 of 5.91 cm3 (17%) in 1 pocket(s) |
| filament that would save | PASS | 0.15 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (3.3, -11.4, 8.1) | 188 | 4.0 | 5.5 | 0.73 |
| 2 | taper | 0.13 mm | (-1.2, -4.8, 8.1) | 194 | 3.8 | 5.4 | 0.71 |
| 3 | taper | 0.13 mm | (0.8, -4.7, 8.1) | 180 | 3.4 | 5.4 | 0.63 |
| 4 | taper | 0.13 mm | (-3.2, -11.6, 8.1) | 167 | 3.4 | 5.5 | 0.62 |
| 5 | taper | 0.13 mm | (0.2, -14.4, 1.5) | 60 | 1.4 | 2.1 | 0.66 |
| 6 | taper | 0.33 mm | (-0.6, -2.0, 3.7) | 15 | 0.3 | 3.1 | 0.11 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
