# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_den_plug.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/den_plug/r0001/thickness-den_plug.md`

part_den_plug.step.py: 9.90 cm3 solid, grid 0.147 mm (250x250x168), 175504 surface samples, thickness resolved to 0.074 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (9 of 175504 samples); thinnest 0.22 mm at (-17.5, -17.7, 23.9) in 3 region(s); no region is a wall, 3 taper(s) at feature edges (0.00% of surface, budget 2%); 23 more within measurement error of the limit |
| thickness distribution | PASS | median 8.23 mm, p95 33.52 mm, max 43.95 mm |
| hollowable at 1.20 mm wall | WARN | 5.75 of 9.90 cm3 (58%) in 3 pocket(s), 2 too small to shell |
| filament that would save | PASS | 0.86 cm3, 1.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.29 mm | (17.5, -17.5, 24.0) | 4 | 0.1 | 0.6 | 0.15 |
| 2 | taper | 0.22 mm | (-17.5, -17.7, 23.9) | 4 | 0.1 | 0.3 | 0.21 |
| 3 | taper | 0.66 mm | (16.6, -12.4, 8.3) | 1 | 0.0 | 0.0 | 0.13 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
