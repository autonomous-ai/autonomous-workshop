# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_den_plug.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/den_plug/r0003/thickness-den_plug.md`

part_den_plug.step.py: 10.16 cm3 solid, grid 0.154 mm (281x260x160), 168155 surface samples, thickness resolved to 0.077 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.08) | PASS | 0.1% of surface below (139 of 168155 samples); thinnest 0.15 mm at (12.9, -19.7, 9.7) in 5 region(s); no region is a wall, 4 taper(s) at feature edges and 1 spot(s) too small to be a wall (0.11% of surface, budget 2%); 17 more within measurement error of the limit |
| thickness distribution | PASS | median 7.72 mm, p95 34.27 mm, max 38.20 mm |
| hollowable at 1.20 mm wall | WARN | 5.58 of 10.16 cm3 (55%) in 2 pocket(s), 5 too small to shell |
| filament that would save | PASS | 0.84 cm3, 1.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.23 mm | (-12.3, -13.1, 7.9) | 68 | 2.2 | 4.7 | 0.47 |
| 2 | spot | 0.23 mm | (11.1, -16.0, 7.9) | 32 | 1.1 | 1.4 | 0.83 |
| 3 | taper | 0.23 mm | (12.8, -12.8, 7.8) | 34 | 1.1 | 1.7 | 0.62 |
| 4 | taper | 0.39 mm | (-11.7, -18.4, 8.5) | 4 | 0.1 | 0.4 | 0.38 |
| 5 | taper | 0.15 mm | (12.9, -19.7, 9.7) | 1 | 0.0 | 0.0 | 0.15 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
