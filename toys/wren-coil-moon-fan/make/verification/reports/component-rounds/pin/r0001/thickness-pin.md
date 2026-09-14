# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_pin.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/pin/r0001/thickness-pin.md`

part_pin.step.py: 0.19 cm3 solid, grid 0.133 mm (65x65x83), 15689 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | FAIL | 3.8% of surface below (512 of 15689 samples); thinnest 0.13 mm at (1.7, 2.1, 9.2) in 5 region(s); no region is a wall, 5 taper(s) at feature edges (3.79% of surface, budget 2%) -- OVER BUDGET; 57 more within measurement error of the limit |
| thickness distribution | PASS | median 1.67 mm, p95 10.27 mm, max 10.40 mm |
| hollowable at 1.20 mm wall | WARN | 0.01 of 0.19 cm3 (3%) in 1 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (-1.7, -2.1, 9.2) | 148 | 3.3 | 5.9 | 0.56 |
| 2 | taper | 0.13 mm | (-0.5, 2.1, 4.5) | 141 | 3.1 | 5.8 | 0.53 |
| 3 | taper | 0.33 mm | (0.6, -2.1, 5.4) | 119 | 2.5 | 5.7 | 0.44 |
| 4 | taper | 0.20 mm | (0.5, 2.1, 4.4) | 103 | 2.5 | 5.9 | 0.43 |
| 5 | taper | 0.13 mm | (1.7, 2.1, 9.2) | 1 | 0.0 | 0.0 | 0.13 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
