# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_body_4.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/thickness-body_4.md`

part_body_4.step.py: 2.79 cm3 solid, grid 0.133 mm (204x260x140), 100094 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (9 of 100094 samples); thinnest 0.13 mm at (-2.4, -3.1, 3.2) in 6 region(s); no region is a wall, 6 taper(s) at feature edges (0.01% of surface, budget 2%); 97 more within measurement error of the limit |
| thickness distribution | PASS | median 6.93 mm, p95 14.67 mm, max 34.07 mm |
| hollowable at 1.20 mm wall | WARN | 0.98 of 2.79 cm3 (35%) in 2 pocket(s) |
| filament that would save | PASS | 0.15 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.20 mm | (-2.5, 3.1, 5.8) | 2 | 0.0 | 0.5 | 0.08 |
| 2 | taper | 0.13 mm | (-4.4, 5.7, 7.3) | 2 | 0.0 | 0.4 | 0.09 |
| 3 | taper | 0.13 mm | (-4.4, -5.6, 7.7) | 2 | 0.0 | 0.4 | 0.10 |
| 4 | taper | 0.13 mm | (-2.4, -3.1, 3.2) | 1 | 0.0 | 0.0 | 0.15 |
| 5 | taper | 0.20 mm | (10.2, -1.2, 14.1) | 1 | 0.0 | 0.0 | 0.13 |
| 6 | taper | 0.53 mm | (-1.6, 2.1, 4.6) | 1 | 0.0 | 0.0 | 0.13 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
