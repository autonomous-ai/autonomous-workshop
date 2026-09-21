# Thickness and hollow

`part_world_saturn_anti.step.py --nozzle 0.4 --report measure/thickness-world_saturn_anti.md`

part_world_saturn_anti.step.py: 14.14 cm3 solid, grid 0.147 mm (236x236x202), 187070 surface samples, thickness resolved to 0.074 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.1% of surface below (126 of 187070 samples); thinnest 0.15 mm at (-8.8, -14.5, 0.0) in 52 region(s); no region is a wall, 50 taper(s) at feature edges and 2 spot(s) too small to be a wall (0.10% of surface, budget 2%); 43 more within measurement error of the limit |
| thickness distribution | PASS | median 25.80 mm, p95 33.52 mm, max 34.62 mm |
| hollowable at 1.20 mm wall | WARN | 9.54 of 14.14 cm3 (67%) in 1 pocket(s) |
| filament that would save | PASS | 1.43 cm3, 1.8 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.15 mm | (-11.1, 12.8, 0.0) | 8 | 0.2 | 2.8 | 0.09 |
| 2 | taper | 0.37 mm | (12.8, -3.0, 23.2) | 3 | 0.2 | 1.0 | 0.24 |
| 3 | taper | 0.22 mm | (11.9, 7.4, 21.7) | 2 | 0.2 | 1.0 | 0.23 |
| 4 | taper | 0.15 mm | (-8.8, -14.5, 0.0) | 9 | 0.2 | 2.8 | 0.07 |
| 5 | taper | 0.15 mm | (5.6, -15.9, 0.0) | 7 | 0.2 | 2.1 | 0.09 |
| 6 | spot | 0.22 mm | (13.5, -2.0, 22.5) | 1 | 0.2 | 0.0 | 1.05 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
