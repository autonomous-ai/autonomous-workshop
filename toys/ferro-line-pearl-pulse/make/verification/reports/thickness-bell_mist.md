# Thickness and hollow

`artifacts/make/r0001/product/cad/part_bell_mist.step.py --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-bell_mist.md`

part_bell_mist.step.py: 0.30 cm3 solid, grid 0.133 mm (173x168x140), 30168 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 1.0% of surface below (310 of 30168 samples); thinnest 0.13 mm at (21.2, 23.4, 6.2) in 14 region(s); no region is a wall, 14 taper(s) at feature edges (0.97% of surface, budget 2%); 53 more within measurement error of the limit |
| thickness distribution | PASS | median 1.20 mm, p95 6.47 mm, max 12.80 mm |
| hollowable at 1.20 mm wall | PASS | 0.00 of 0.30 cm3 (0%) in 0 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.33 mm | (30.3, 26.5, 18.0) | 270 | 4.7 | 9.8 | 0.47 |
| 2 | taper | 0.13 mm | (25.5, 28.2, 17.3) | 18 | 0.4 | 2.4 | 0.17 |
| 3 | taper | 0.53 mm | (24.5, 27.0, 14.6) | 4 | 0.1 | 0.6 | 0.20 |
| 4 | taper | 0.20 mm | (21.7, 24.0, 9.2) | 4 | 0.1 | 0.2 | 0.31 |
| 5 | taper | 0.20 mm | (23.3, 25.9, 12.4) | 3 | 0.1 | 0.6 | 0.10 |
| 6 | taper | 0.13 mm | (19.5, 21.7, 3.1) | 2 | 0.0 | 0.0 | 0.34 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
