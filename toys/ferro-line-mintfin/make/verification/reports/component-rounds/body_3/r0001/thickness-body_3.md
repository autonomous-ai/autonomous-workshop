# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_body_3.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/body_3/r0001/thickness-body_3.md`

part_body_3.step.py: 2.55 cm3 solid, grid 0.133 mm (204x177x140), 86373 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (10 of 86373 samples); thinnest 0.13 mm at (-2.7, -3.5, 2.7) in 4 region(s); no region is a wall, 4 taper(s) at feature edges (0.01% of surface, budget 2%); 87 more within measurement error of the limit |
| thickness distribution | PASS | median 7.53 mm, p95 14.00 mm, max 23.60 mm |
| hollowable at 1.20 mm wall | WARN | 0.96 of 2.55 cm3 (38%) in 2 pocket(s), 1 too small to shell |
| filament that would save | PASS | 0.14 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.40 mm | (-4.4, 5.7, 7.6) | 5 | 0.1 | 0.6 | 0.16 |
| 2 | taper | 0.13 mm | (-2.7, -3.5, 2.7) | 2 | 0.0 | 0.2 | 0.17 |
| 3 | taper | 0.27 mm | (10.2, 1.2, 14.1) | 2 | 0.0 | 0.1 | 0.27 |
| 4 | taper | 0.40 mm | (10.2, -1.1, 14.3) | 1 | 0.0 | 0.0 | 0.13 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
