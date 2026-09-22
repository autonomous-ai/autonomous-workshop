# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_body_2.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/thickness-body_2.md`

part_body_2.step.py: 2.76 cm3 solid, grid 0.133 mm (204x185x147), 91506 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (11 of 91506 samples); thinnest 0.13 mm at (-2.6, 3.3, 6.0) in 5 region(s); no region is a wall, 5 taper(s) at feature edges (0.01% of surface, budget 2%); 97 more within measurement error of the limit |
| thickness distribution | PASS | median 7.67 mm, p95 14.93 mm, max 24.67 mm |
| hollowable at 1.20 mm wall | WARN | 1.08 of 2.76 cm3 (39%) in 2 pocket(s) |
| filament that would save | PASS | 0.16 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (-2.6, 3.3, 6.0) | 3 | 0.1 | 0.8 | 0.08 |
| 2 | taper | 0.60 mm | (10.2, -1.1, 15.0) | 3 | 0.1 | 0.2 | 0.23 |
| 3 | taper | 0.53 mm | (-4.4, 5.7, 7.6) | 2 | 0.0 | 0.1 | 0.28 |
| 4 | taper | 0.13 mm | (-4.4, -5.7, 7.5) | 2 | 0.0 | 0.4 | 0.08 |
| 5 | taper | 0.33 mm | (-2.3, -2.9, 3.5) | 1 | 0.0 | 0.0 | 0.14 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
