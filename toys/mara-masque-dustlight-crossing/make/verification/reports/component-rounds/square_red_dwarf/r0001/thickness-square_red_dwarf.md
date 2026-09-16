# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_square_red_dwarf.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/square_red_dwarf/r0001/thickness-square_red_dwarf.md`

part_square_red_dwarf.step.py: 3.34 cm3 solid, grid 0.133 mm (170x170x200), 105259 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.3% of surface below (173 of 105259 samples); thinnest 0.13 mm at (-7.6, 0.0, 16.0) in 5 region(s); no region is a wall, 5 taper(s) at feature edges (0.30% of surface, budget 2%); 235 more within measurement error of the limit |
| thickness distribution | PASS | median 7.13 mm, p95 23.60 mm, max 26.93 mm |
| hollowable at 1.20 mm wall | WARN | 1.26 of 3.34 cm3 (38%) in 1 pocket(s) |
| filament that would save | PASS | 0.19 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.73 mm | (-0.8, 5.4, 3.3) | 46 | 1.6 | 2.9 | 0.54 |
| 2 | taper | 0.73 mm | (0.0, 9.6, 3.3) | 42 | 1.6 | 2.8 | 0.56 |
| 3 | taper | 0.73 mm | (-0.7, -4.6, 3.3) | 42 | 1.5 | 2.9 | 0.53 |
| 4 | taper | 0.73 mm | (1.3, -10.4, 3.4) | 42 | 1.5 | 3.0 | 0.51 |
| 5 | taper | 0.13 mm | (-7.6, 0.0, 16.0) | 1 | 0.0 | 0.0 | 0.13 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
