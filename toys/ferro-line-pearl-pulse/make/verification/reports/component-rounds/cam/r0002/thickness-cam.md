# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_cam.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/cam/r0002/thickness-cam.md`

part_cam.step.py: 3.97 cm3 solid, grid 0.133 mm (350x275x54), 150798 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | FAIL | 0.3% of surface below (279 of 150798 samples); thinnest 0.13 mm at (19.9, -1.9, 3.4) in 21 region(s); 2 wall(s) (widest band 1.09 mm), 17 taper(s) at feature edges and 2 spot(s) too small to be a wall (0.09% of surface, budget 2%); 166 more within measurement error of the limit |
| thickness distribution | PASS | median 4.33 mm, p95 15.73 mm, max 46.00 mm |
| hollowable at 1.20 mm wall | WARN | 1.18 of 3.97 cm3 (30%) in 2 pocket(s) |
| filament that would save | PASS | 0.18 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.20 mm | (19.0, -0.4, 3.5) | 93 | 2.9 | 2.7 | 1.09 |
| 2 | wall | 0.13 mm | (-21.1, 0.6, 3.6) | 93 | 2.8 | 2.8 | 1.01 |
| 3 | spot | 0.20 mm | (21.0, -0.4, 3.3) | 28 | 0.9 | 0.8 | 1.07 |
| 4 | spot | 0.13 mm | (-18.9, 0.5, 3.1) | 19 | 0.7 | 0.8 | 0.88 |
| 5 | taper | 0.13 mm | (19.9, -1.9, 3.4) | 7 | 0.2 | 0.5 | 0.41 |
| 6 | taper | 0.47 mm | (-19.9, 1.8, 3.2) | 8 | 0.2 | 0.5 | 0.40 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
