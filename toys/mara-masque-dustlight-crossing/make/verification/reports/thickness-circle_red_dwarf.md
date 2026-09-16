# Thickness and hollow

`artifacts/make/r0001/product/cad/part_circle_red_dwarf.step.py --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-circle_red_dwarf.md`

part_circle_red_dwarf.step.py: 3.06 cm3 solid, grid 0.133 mm (170x170x200), 94356 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.4% of surface below (185 of 94356 samples); thinnest 0.73 mm at (0.4, -10.4, 3.4) in 4 region(s); no region is a wall, 4 taper(s) at feature edges (0.35% of surface, budget 2%); 233 more within measurement error of the limit |
| thickness distribution | PASS | median 9.33 mm, p95 22.00 mm, max 26.00 mm |
| hollowable at 1.20 mm wall | WARN | 1.20 of 3.06 cm3 (39%) in 1 pocket(s) |
| filament that would save | PASS | 0.18 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.73 mm | (0.4, -10.4, 3.4) | 50 | 1.7 | 3.0 | 0.57 |
| 2 | taper | 0.73 mm | (0.1, -4.6, 3.3) | 46 | 1.6 | 3.0 | 0.54 |
| 3 | taper | 0.73 mm | (-1.3, 5.4, 3.6) | 42 | 1.6 | 2.8 | 0.56 |
| 4 | taper | 0.73 mm | (-1.0, 9.6, 3.6) | 47 | 1.6 | 2.8 | 0.57 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
