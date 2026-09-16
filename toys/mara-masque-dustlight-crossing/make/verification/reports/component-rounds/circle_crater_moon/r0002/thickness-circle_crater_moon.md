# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_circle_crater_moon.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/circle_crater_moon/r0002/thickness-circle_crater_moon.md`

part_circle_crater_moon.step.py: 2.73 cm3 solid, grid 0.133 mm (170x170x170), 89843 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.6% of surface below (256 of 89843 samples); thinnest 0.13 mm at (-5.6, -3.2, 9.7) in 10 region(s); no region is a wall, 10 taper(s) at feature edges (0.58% of surface, budget 2%); 258 more within measurement error of the limit |
| thickness distribution | PASS | median 7.33 mm, p95 21.93 mm, max 22.07 mm |
| hollowable at 1.20 mm wall | WARN | 1.02 of 2.73 cm3 (37%) in 1 pocket(s) |
| filament that would save | PASS | 0.15 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (3.1, -3.8, 15.4) | 82 | 2.0 | 4.9 | 0.41 |
| 2 | taper | 0.73 mm | (0.6, -4.6, 3.5) | 34 | 1.7 | 2.8 | 0.60 |
| 3 | taper | 0.73 mm | (-1.2, 9.6, 3.5) | 47 | 1.6 | 2.8 | 0.56 |
| 4 | taper | 0.73 mm | (-0.3, 5.4, 3.4) | 40 | 1.6 | 2.8 | 0.56 |
| 5 | taper | 0.73 mm | (0.1, -10.4, 3.4) | 31 | 1.5 | 2.9 | 0.52 |
| 6 | taper | 0.13 mm | (-5.6, -3.2, 9.7) | 10 | 0.8 | 2.1 | 0.39 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
