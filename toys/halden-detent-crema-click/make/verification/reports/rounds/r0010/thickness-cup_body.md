# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/crema_click/part_cup_body.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/crema_click/measure/rounds/r0010/thickness-cup_body.md`

part_cup_body.step.py: 100.23 cm3 solid, grid 0.277 mm (286x236x165), 268755 surface samples, thickness resolved to 0.139 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.14) | PASS | 0.0% of surface below (45 of 268755 samples); thinnest 0.28 mm at (10.3, -17.5, 4.8) in 4 region(s); no region is a wall, 4 taper(s) at feature edges (0.02% of surface, budget 2%); 15 more within measurement error of the limit |
| thickness distribution | PASS | median 20.37 mm, p95 44.35 mm, max 46.71 mm |
| hollowable at 1.20 mm wall | WARN | 75.45 of 100.23 cm3 (75%) in 1 pocket(s) |
| filament that would save | PASS | 11.32 cm3, 14.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.42 mm | (-10.2, -17.3, 0.3) | 10 | 1.9 | 4.3 | 0.44 |
| 2 | taper | 0.28 mm | (10.3, 17.4, 4.3) | 16 | 1.4 | 4.1 | 0.33 |
| 3 | taper | 0.28 mm | (10.3, -17.5, 4.8) | 9 | 1.2 | 3.6 | 0.34 |
| 4 | taper | 0.28 mm | (-10.3, 17.4, 3.8) | 10 | 0.9 | 2.2 | 0.41 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
