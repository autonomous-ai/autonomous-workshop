# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_mount_pin.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/thickness-mount_pin.md`

part_mount_pin.step.py: 1.01 cm3 solid, grid 0.133 mm (95x95x141), 42126 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.8% of surface below (326 of 42126 samples); thinnest 0.13 mm at (1.4, -3.7, 14.9) in 4 region(s); no region is a wall, 4 taper(s) at feature edges (0.79% of surface, budget 2%); 53 more within measurement error of the limit |
| thickness distribution | PASS | median 7.93 mm, p95 18.13 mm, max 18.13 mm |
| hollowable at 1.20 mm wall | WARN | 0.28 of 1.01 cm3 (27%) in 1 pocket(s) |
| filament that would save | PASS | 0.04 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (1.5, 3.7, 14.7) | 94 | 1.8 | 2.7 | 0.67 |
| 2 | taper | 0.13 mm | (1.4, -3.7, 14.9) | 93 | 1.8 | 2.6 | 0.68 |
| 3 | taper | 0.13 mm | (-1.5, 3.7, 14.9) | 76 | 1.4 | 2.8 | 0.51 |
| 4 | taper | 0.13 mm | (-1.5, -3.7, 13.6) | 63 | 1.2 | 2.7 | 0.43 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
