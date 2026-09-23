# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_main_pin.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/main_pin/r0002/thickness-main_pin.md`

part_main_pin.step.py: 1.53 cm3 solid, grid 0.133 mm (95x95x219), 56848 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.7% of surface below (369 of 56848 samples); thinnest 0.13 mm at (1.5, -3.7, 25.0) in 4 region(s); no region is a wall, 4 taper(s) at feature edges (0.67% of surface, budget 2%); 57 more within measurement error of the limit |
| thickness distribution | PASS | median 7.93 mm, p95 28.53 mm, max 28.53 mm |
| hollowable at 1.20 mm wall | WARN | 0.52 of 1.53 cm3 (34%) in 1 pocket(s) |
| filament that would save | PASS | 0.08 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (1.5, 3.7, 24.9) | 101 | 1.9 | 2.8 | 0.68 |
| 2 | taper | 0.13 mm | (-1.5, 3.7, 24.4) | 96 | 1.8 | 2.8 | 0.65 |
| 3 | taper | 0.13 mm | (1.5, -3.7, 25.0) | 91 | 1.7 | 2.8 | 0.62 |
| 4 | taper | 0.13 mm | (-1.5, -3.7, 24.6) | 81 | 1.6 | 2.8 | 0.57 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
