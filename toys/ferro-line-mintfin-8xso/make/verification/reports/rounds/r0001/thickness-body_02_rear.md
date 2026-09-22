# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_02_rear.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/rounds/r0001/thickness-body_02_rear.md`

part_body_02_rear.step.py: 5.91 cm3 solid, grid 0.133 mm (452x334x66), 256843 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.4% of surface below (850 of 256843 samples); thinnest 0.13 mm at (-4.9, -12.9, 0.1) in 27 region(s); no region is a wall, 27 taper(s) at feature edges (0.37% of surface, budget 2%); 180 more within measurement error of the limit |
| thickness distribution | PASS | median 3.13 mm, p95 19.93 mm, max 59.60 mm |
| hollowable at 1.20 mm wall | WARN | 0.98 of 5.91 cm3 (17%) in 1 pocket(s) |
| filament that would save | PASS | 0.15 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (-4.1, -9.7, 8.1) | 189 | 3.9 | 5.5 | 0.71 |
| 2 | taper | 0.13 mm | (3.3, -11.3, 8.1) | 186 | 3.9 | 5.4 | 0.72 |
| 3 | taper | 0.13 mm | (3.7, -6.9, 8.1) | 191 | 3.7 | 5.4 | 0.70 |
| 4 | taper | 0.13 mm | (-0.6, -4.6, 8.1) | 174 | 3.2 | 5.4 | 0.59 |
| 5 | taper | 0.13 mm | (0.4, -14.4, 1.5) | 59 | 1.3 | 2.1 | 0.64 |
| 6 | taper | 0.20 mm | (-0.6, -2.0, 3.8) | 11 | 0.2 | 1.9 | 0.12 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
