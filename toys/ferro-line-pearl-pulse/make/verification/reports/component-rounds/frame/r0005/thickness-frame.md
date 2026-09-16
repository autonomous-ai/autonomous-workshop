# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_frame.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/frame/r0005/thickness-frame.md`

part_frame.step.py: 7.45 cm3 solid, grid 0.228 mm (292x292x128), 192021 surface samples, thickness resolved to 0.114 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.11) | PASS | 0.1% of surface below (87 of 192021 samples); thinnest 0.23 mm at (19.4, 16.5, 2.2) in 27 region(s); no region is a wall, 25 taper(s) at feature edges and 2 spot(s) too small to be a wall (0.06% of surface, budget 2%); 1 more within measurement error of the limit |
| thickness distribution | PASS | median 1.94 mm, p95 8.78 mm, max 36.72 mm |
| hollowable at 1.20 mm wall | WARN | 0.01 of 7.45 cm3 (0%) in 1 pocket(s), 3 too small to shell |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.68 mm | (2.8, -28.9, 17.2) | 8 | 0.6 | 0.9 | 0.71 |
| 2 | spot | 0.68 mm | (29.0, -2.8, 17.2) | 7 | 0.5 | 0.5 | 1.02 |
| 3 | taper | 0.68 mm | (3.2, 28.9, 17.2) | 7 | 0.5 | 0.9 | 0.54 |
| 4 | taper | 0.23 mm | (19.0, 21.9, 16.5) | 6 | 0.5 | 1.5 | 0.32 |
| 5 | taper | 0.68 mm | (29.0, 2.5, 17.2) | 6 | 0.5 | 0.7 | 0.68 |
| 6 | taper | 0.23 mm | (21.9, -19.1, 16.4) | 6 | 0.5 | 1.4 | 0.34 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
