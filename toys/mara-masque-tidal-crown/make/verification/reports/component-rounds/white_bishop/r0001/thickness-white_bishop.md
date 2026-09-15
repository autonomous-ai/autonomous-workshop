# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_white_bishop.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/white_bishop/r0001/thickness-white_bishop.md`

part_white_bishop.step.py: 1.25 cm3 solid, grid 0.133 mm (110x110x177), 50328 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | FAIL | 0.7% of surface below (314 of 50328 samples); thinnest 0.13 mm at (1.9, 3.5, 10.0) in 2 region(s); 1 wall(s) (widest band 1.31 mm), 1 taper(s) at feature edges (0.00% of surface, budget 2%); 27 more within measurement error of the limit |
| thickness distribution | PASS | median 5.60 mm, p95 14.00 mm, max 22.93 mm |
| hollowable at 1.20 mm wall | WARN | 0.36 of 1.25 cm3 (29%) in 1 pocket(s) |
| filament that would save | PASS | 0.05 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.13 mm | (4.0, -2.4, 18.7) | 313 | 6.3 | 4.8 | 1.31 |
| 2 | taper | 0.13 mm | (1.9, 3.5, 10.0) | 1 | 0.0 | 0.0 | 0.13 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
