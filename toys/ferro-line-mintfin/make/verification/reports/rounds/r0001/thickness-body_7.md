# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_body_7.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/thickness-body_7.md`

part_body_7.step.py: 1.77 cm3 solid, grid 0.133 mm (204x132x117), 69642 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (14 of 69642 samples); thinnest 0.13 mm at (-2.2, -2.8, 3.6) in 7 region(s); no region is a wall, 7 taper(s) at feature edges (0.02% of surface, budget 2%); 91 more within measurement error of the limit |
| thickness distribution | PASS | median 6.40 mm, p95 14.93 mm, max 19.27 mm |
| hollowable at 1.20 mm wall | WARN | 0.53 of 1.77 cm3 (30%) in 2 pocket(s) |
| filament that would save | PASS | 0.08 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (-4.4, 5.7, 7.6) | 4 | 0.1 | 0.6 | 0.13 |
| 2 | taper | 0.67 mm | (10.2, 1.1, 12.2) | 2 | 0.1 | 0.4 | 0.14 |
| 3 | taper | 0.13 mm | (10.2, 1.2, 11.0) | 3 | 0.1 | 0.3 | 0.21 |
| 4 | taper | 0.13 mm | (-2.2, -2.8, 3.6) | 2 | 0.0 | 0.2 | 0.20 |
| 5 | taper | 0.60 mm | (10.2, 1.1, 13.4) | 1 | 0.0 | 0.0 | 0.23 |
| 6 | taper | 0.20 mm | (-2.3, 3.0, 5.6) | 1 | 0.0 | 0.0 | 0.14 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
