# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_frame.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/frame/r0002/thickness-frame.md`

part_frame.step.py: 7.52 cm3 solid, grid 0.228 mm (292x292x128), 194072 surface samples, thickness resolved to 0.114 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.11) | PASS | 0.1% of surface below (86 of 194072 samples); thinnest 0.23 mm at (-24.5, -19.4, 13.5) in 30 region(s); no region is a wall, 29 taper(s) at feature edges and 1 spot(s) too small to be a wall (0.06% of surface, budget 2%); 3 more within measurement error of the limit |
| thickness distribution | PASS | median 1.94 mm, p95 8.78 mm, max 36.72 mm |
| hollowable at 1.20 mm wall | WARN | 0.01 of 7.52 cm3 (0%) in 1 pocket(s), 3 too small to shell |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.68 mm | (-28.9, -2.6, 17.2) | 7 | 0.5 | 0.9 | 0.58 |
| 2 | taper | 0.68 mm | (-22.8, -18.3, 17.2) | 6 | 0.5 | 0.8 | 0.55 |
| 3 | taper | 0.68 mm | (-3.2, -29.1, 17.2) | 6 | 0.4 | 0.9 | 0.49 |
| 4 | taper | 0.68 mm | (-2.7, 29.0, 17.2) | 5 | 0.4 | 0.7 | 0.53 |
| 5 | taper | 0.23 mm | (-20.6, -17.6, 2.5) | 6 | 0.4 | 0.8 | 0.50 |
| 6 | taper | 0.68 mm | (28.9, 2.7, 17.2) | 5 | 0.4 | 0.8 | 0.48 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
