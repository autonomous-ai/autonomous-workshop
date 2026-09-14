# Thickness and hollow

`part_canopy_cap.step.py --nozzle 0.4 --report measure/thickness-canopy_cap.md`

part_canopy_cap.step.py: 15.47 cm3 solid, grid 0.197 mm (816x735x20), 351504 surface samples, thickness resolved to 0.098 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.10) | PASS | 0.0% of surface below (61 of 351504 samples); thinnest 0.59 mm at (6.2, 70.3, 0.0) in 13 region(s); no region is a wall, 13 taper(s) at feature edges (0.02% of surface, budget 2%); 312 more within measurement error of the limit |
| thickness distribution | PASS | median 2.95 mm, p95 7.98 mm, max 159.76 mm |
| hollowable at 1.20 mm wall | WARN | 2.06 of 15.47 cm3 (13%) in 1 pocket(s) |
| filament that would save | PASS | 0.31 cm3, 0.4 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.59 mm | (154.0, 70.6, 0.0) | 11 | 0.5 | 3.0 | 0.16 |
| 2 | taper | 0.59 mm | (6.2, 70.3, 0.0) | 11 | 0.5 | 3.0 | 0.16 |
| 3 | taper | 0.59 mm | (78.9, 5.9, 0.0) | 11 | 0.4 | 5.4 | 0.08 |
| 4 | taper | 0.59 mm | (150.2, 70.3, 0.0) | 9 | 0.3 | 3.4 | 0.10 |
| 5 | taper | 0.59 mm | (79.8, 138.3, 0.0) | 6 | 0.2 | 1.4 | 0.18 |
| 6 | taper | 0.59 mm | (78.2, 9.8, 0.0) | 3 | 0.1 | 2.3 | 0.05 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
