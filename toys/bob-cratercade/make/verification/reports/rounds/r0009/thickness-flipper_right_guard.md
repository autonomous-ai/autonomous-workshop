# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_flipper_right_guard.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0009/thickness-flipper_right_guard.md`

part_flipper_right_guard.step.py: 9.81 cm3 solid, grid 0.197 mm (398x259x116), 210119 surface samples, thickness resolved to 0.098 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.10) | PASS | 0.0% of surface below (67 of 210119 samples); thinnest 0.59 mm at (22.5, 14.2, 22.0) in 4 region(s); no region is a wall, 4 taper(s) at feature edges (0.03% of surface, budget 2%); 214 more within measurement error of the limit |
| thickness distribution | PASS | median 2.95 mm, p95 22.46 mm, max 75.45 mm |
| hollowable at 1.20 mm wall | WARN | 1.24 of 9.81 cm3 (13%) in 2 pocket(s) |
| filament that would save | PASS | 0.19 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.59 mm | (22.5, 14.2, 22.0) | 27 | 1.1 | 5.9 | 0.18 |
| 2 | taper | 0.59 mm | (-40.6, 25.4, 22.0) | 25 | 1.0 | 6.9 | 0.15 |
| 3 | taper | 0.59 mm | (-41.0, 27.6, 22.0) | 9 | 0.4 | 2.4 | 0.15 |
| 4 | taper | 0.59 mm | (23.7, 12.7, 22.0) | 6 | 0.2 | 3.5 | 0.07 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
