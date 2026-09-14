# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_single_08.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/thickness-single_08.md`

part_single_08.step.py: 0.24 cm3 solid, grid 0.133 mm (95x65x35), 13478 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (5 of 13478 samples); thinnest 0.33 mm at (5.5, -1.9, 0.0) in 4 region(s); no region is a wall, 4 taper(s) at feature edges (0.04% of surface, budget 2%); 2 more within measurement error of the limit |
| thickness distribution | PASS | median 4.00 mm, p95 9.20 mm, max 12.13 mm |
| hollowable at 1.20 mm wall | WARN | 0.04 of 0.24 cm3 (18%) in 1 pocket(s) |
| filament that would save | PASS | 0.01 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.67 mm | (2.5, 3.9, 0.2) | 2 | 0.0 | 0.0 | 0.28 |
| 2 | taper | 0.60 mm | (5.9, 0.4, 0.2) | 1 | 0.0 | 0.0 | 0.22 |
| 3 | taper | 0.33 mm | (5.5, -1.9, 0.0) | 1 | 0.0 | 0.0 | 0.13 |
| 4 | taper | 0.73 mm | (-1.2, -2.7, 3.9) | 1 | 0.0 | 0.0 | 0.12 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
