# Thickness and hollow

`artifacts/make/r0001/product/cad/part_cam.step.py --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-cam.md`

part_cam.step.py: 3.98 cm3 solid, grid 0.133 mm (350x275x54), 150996 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.1% of surface below (132 of 150996 samples); thinnest 0.13 mm at (-21.2, -0.0, 3.7) in 19 region(s); no region is a wall, 16 taper(s) at feature edges and 3 spot(s) too small to be a wall (0.13% of surface, budget 2%); 17 more within measurement error of the limit |
| thickness distribution | PASS | median 4.33 mm, p95 15.73 mm, max 46.00 mm |
| hollowable at 1.20 mm wall | WARN | 1.18 of 3.98 cm3 (30%) in 2 pocket(s) |
| filament that would save | PASS | 0.18 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | spot | 0.20 mm | (21.3, -0.0, 3.6) | 29 | 0.9 | 0.8 | 1.10 |
| 2 | spot | 0.13 mm | (-21.2, -0.0, 3.7) | 30 | 0.8 | 0.9 | 0.98 |
| 3 | spot | 0.13 mm | (-18.7, 0.1, 3.6) | 23 | 0.8 | 0.9 | 0.87 |
| 4 | taper | 0.20 mm | (18.8, -0.0, 3.7) | 22 | 0.7 | 0.9 | 0.79 |
| 5 | taper | 0.33 mm | (5.1, -2.0, 3.3) | 6 | 0.1 | 0.8 | 0.14 |
| 6 | taper | 0.47 mm | (-16.9, 5.8, 6.4) | 4 | 0.1 | 1.3 | 0.06 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
