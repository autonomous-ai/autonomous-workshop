# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_cam.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/cam/r0001/thickness-cam.md`

part_cam.step.py: 4.08 cm3 solid, grid 0.133 mm (357x275x54), 150244 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (33 of 150244 samples); thinnest 0.13 mm at (4.8, -2.4, 3.3) in 16 region(s); no region is a wall, 16 taper(s) at feature edges (0.02% of surface, budget 2%); 8 more within measurement error of the limit |
| thickness distribution | PASS | median 4.27 mm, p95 16.07 mm, max 46.93 mm |
| hollowable at 1.20 mm wall | WARN | 1.21 of 4.08 cm3 (30%) in 2 pocket(s) |
| filament that would save | PASS | 0.18 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.60 mm | (-14.4, -10.5, 6.1) | 5 | 0.1 | 2.0 | 0.05 |
| 2 | taper | 0.53 mm | (5.3, 0.9, 3.1) | 2 | 0.1 | 0.6 | 0.10 |
| 3 | taper | 0.47 mm | (-18.0, -0.4, 6.4) | 3 | 0.1 | 0.1 | 0.43 |
| 4 | taper | 0.40 mm | (-15.9, 8.4, 6.2) | 3 | 0.1 | 0.7 | 0.08 |
| 5 | taper | 0.53 mm | (-17.1, -5.7, 6.3) | 3 | 0.1 | 1.4 | 0.04 |
| 6 | taper | 0.53 mm | (4.9, 2.6, 3.3) | 3 | 0.1 | 0.9 | 0.06 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
