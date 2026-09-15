# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_jackpot_rocker.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0008/thickness-jackpot_rocker.md`

part_jackpot_rocker.step.py: 22.86 cm3 solid, grid 0.337 mm (223x324x165), 100491 surface samples, thickness resolved to 0.168 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.17) | FAIL | 0.1% of surface below (57 of 100491 samples); thinnest 0.34 mm at (-15.6, 4.5, 35.5) in 5 region(s); 1 wall(s) (widest band 1.07 mm), 4 taper(s) at feature edges (0.05% of surface, budget 2%); 43 more within measurement error of the limit |
| thickness distribution | PASS | median 3.71 mm, p95 32.01 mm, max 74.63 mm |
| hollowable at 1.20 mm wall | WARN | 9.64 of 22.86 cm3 (42%) in 2 pocket(s) |
| filament that would save | PASS | 1.45 cm3, 1.8 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.34 mm | (-6.1, 4.0, 17.6) | 24 | 2.9 | 14.2 | 0.21 |
| 2 | taper | 0.34 mm | (6.9, 4.0, 17.6) | 14 | 1.7 | 7.7 | 0.23 |
| 3 | wall | 0.34 mm | (15.3, 4.0, 35.6) | 9 | 1.7 | 1.6 | 1.07 |
| 4 | taper | 0.34 mm | (-15.6, 4.5, 35.5) | 6 | 1.0 | 1.3 | 0.76 |
| 5 | taper | 0.34 mm | (-12.3, 4.0, 17.6) | 4 | 0.5 | 0.9 | 0.52 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
