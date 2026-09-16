# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_square_crater_moon.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/thickness-square_crater_moon.md`

part_square_crater_moon.step.py: 3.01 cm3 solid, grid 0.133 mm (170x170x170), 100647 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.5% of surface below (288 of 100647 samples); thinnest 0.13 mm at (-5.6, -3.1, 9.7) in 10 region(s); no region is a wall, 9 taper(s) at feature edges and 1 spot(s) too small to be a wall (0.55% of surface, budget 2%); 284 more within measurement error of the limit |
| thickness distribution | PASS | median 6.87 mm, p95 22.00 mm, max 26.93 mm |
| hollowable at 1.20 mm wall | WARN | 1.08 of 3.01 cm3 (36%) in 1 pocket(s) |
| filament that would save | PASS | 0.16 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (3.8, -3.9, 13.1) | 102 | 2.5 | 5.9 | 0.42 |
| 2 | taper | 0.73 mm | (1.1, -4.6, 3.5) | 41 | 1.6 | 2.9 | 0.55 |
| 3 | taper | 0.73 mm | (0.7, 9.6, 3.4) | 39 | 1.6 | 2.9 | 0.55 |
| 4 | taper | 0.73 mm | (0.1, 5.4, 3.4) | 41 | 1.6 | 2.8 | 0.57 |
| 5 | taper | 0.73 mm | (1.0, -10.4, 3.5) | 43 | 1.5 | 3.0 | 0.52 |
| 6 | taper | 0.13 mm | (-5.6, -3.1, 9.7) | 13 | 1.0 | 2.3 | 0.43 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
