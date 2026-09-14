# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_mission_crater.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0004/thickness-mission_crater.md`

part_mission_crater.step.py: 11.76 cm3 solid, grid 0.133 mm (320x320x110), 265180 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.6% of surface below (1379 of 265180 samples); thinnest 0.13 mm at (-9.5, -6.1, 12.2) in 8 region(s); no region is a wall, 8 taper(s) at feature edges (0.59% of surface, budget 2%); 211 more within measurement error of the limit |
| thickness distribution | PASS | median 8.80 mm, p95 41.93 mm, max 42.07 mm |
| hollowable at 1.20 mm wall | WARN | 6.28 of 11.76 cm3 (53%) in 1 pocket(s) |
| filament that would save | PASS | 0.94 cm3, 1.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (12.7, -6.0, 8.4) | 285 | 6.1 | 10.3 | 0.59 |
| 2 | taper | 0.13 mm | (9.4, 6.1, 12.4) | 289 | 6.0 | 10.3 | 0.59 |
| 3 | taper | 0.13 mm | (-9.5, -6.1, 12.2) | 288 | 6.0 | 10.2 | 0.59 |
| 4 | taper | 0.20 mm | (-11.2, 6.0, 10.1) | 286 | 6.0 | 10.2 | 0.59 |
| 5 | taper | 0.13 mm | (18.4, -6.0, 9.0) | 76 | 1.6 | 4.0 | 0.41 |
| 6 | taper | 0.13 mm | (-18.8, -6.0, 8.2) | 72 | 1.5 | 4.2 | 0.37 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
