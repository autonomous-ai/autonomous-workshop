# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/heritage/part_screen.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/heritage/measure/rounds/r0001/thickness-screen.md`

part_screen.step.py: 3.16 cm3 solid, grid 0.133 mm (290x323x27), 163809 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.1% of surface below (109 of 163809 samples); thinnest 0.53 mm at (-13.7, 37.5, 0.1) in 7 region(s); no region is a wall, 7 taper(s) at feature edges (0.07% of surface, budget 2%); 15 more within measurement error of the limit |
| thickness distribution | PASS | median 2.40 mm, p95 33.73 mm, max 42.40 mm |
| hollowable at 1.20 mm wall | WARN | 0.01 of 3.16 cm3 (0%) in 1 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.53 mm | (-13.7, 37.5, 0.1) | 34 | 0.6 | 8.3 | 0.08 |
| 2 | taper | 0.67 mm | (6.5, 37.5, 0.1) | 27 | 0.5 | 5.0 | 0.10 |
| 3 | taper | 0.60 mm | (-0.2, 37.5, 0.1) | 22 | 0.4 | 4.7 | 0.09 |
| 4 | taper | 0.67 mm | (-4.0, 37.5, 0.1) | 12 | 0.2 | 3.0 | 0.08 |
| 5 | taper | 0.67 mm | (14.2, 37.5, 0.1) | 8 | 0.2 | 2.3 | 0.07 |
| 6 | taper | 0.67 mm | (10.5, 37.3, 0.0) | 3 | 0.1 | 1.2 | 0.05 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
