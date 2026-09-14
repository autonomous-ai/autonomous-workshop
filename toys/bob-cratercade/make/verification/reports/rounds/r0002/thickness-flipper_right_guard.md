# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_flipper_right_guard.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0002/thickness-flipper_right_guard.md`

part_flipper_right_guard.step.py: 9.71 cm3 solid, grid 0.197 mm (398x259x116), 208193 surface samples, thickness resolved to 0.098 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.10) | FAIL | 0.3% of surface below (443 of 208193 samples); thinnest 0.20 mm at (19.0, 8.1, 1.8) in 9 region(s); 4 wall(s) (widest band 1.90 mm), 5 taper(s) at feature edges (0.04% of surface, budget 2%); 234 more within measurement error of the limit |
| thickness distribution | PASS | median 2.95 mm, p95 22.85 mm, max 75.05 mm |
| hollowable at 1.20 mm wall | WARN | 1.24 of 9.71 cm3 (13%) in 2 pocket(s) |
| filament that would save | PASS | 0.19 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.20 mm | (-46.9, 28.6, 1.9) | 104 | 5.3 | 2.8 | 1.90 |
| 2 | wall | 0.20 mm | (-46.9, 23.4, 0.6) | 102 | 5.1 | 2.9 | 1.72 |
| 3 | wall | 0.20 mm | (19.0, 8.1, 1.8) | 92 | 4.8 | 2.9 | 1.69 |
| 4 | wall | 0.20 mm | (24.0, 8.1, 0.5) | 72 | 3.7 | 2.7 | 1.39 |
| 5 | taper | 0.59 mm | (23.0, 13.9, 22.0) | 28 | 1.2 | 5.9 | 0.20 |
| 6 | taper | 0.39 mm | (-44.6, 24.4, 22.0) | 21 | 0.8 | 4.9 | 0.17 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
