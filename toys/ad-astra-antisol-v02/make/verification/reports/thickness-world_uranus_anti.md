# Thickness and hollow

`cad/part_world_uranus_anti.step.py --nozzle 0.4 --report cad/measure/thickness-world_uranus_anti.md`

part_world_uranus_anti.step.py: 9.91 cm3 solid, grid 0.140 mm (247x248x184), 172481 surface samples, thickness resolved to 0.070 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.1% of surface below (174 of 172481 samples); thinnest 0.14 mm at (-16.5, -4.2, 0.0) in 35 region(s); no region is a wall, 35 taper(s) at feature edges (0.13% of surface, budget 2%); 1 more within measurement error of the limit |
| thickness distribution | PASS | median 21.84 mm, p95 33.46 mm, max 33.81 mm |
| hollowable at 1.20 mm wall | WARN | 6.08 of 9.91 cm3 (61%) in 1 pocket(s) |
| filament that would save | PASS | 0.91 cm3, 1.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.28 mm | (-10.4, 13.3, 0.0) | 23 | 0.5 | 5.6 | 0.09 |
| 2 | taper | 0.14 mm | (-12.6, -11.3, 0.0) | 10 | 0.4 | 3.2 | 0.11 |
| 3 | taper | 0.14 mm | (-1.6, -16.8, 0.0) | 8 | 0.2 | 1.6 | 0.15 |
| 4 | taper | 0.14 mm | (-8.4, -14.7, 0.0) | 12 | 0.2 | 1.4 | 0.17 |
| 5 | taper | 0.42 mm | (16.3, 4.5, 0.0) | 7 | 0.2 | 1.7 | 0.14 |
| 6 | taper | 0.28 mm | (4.6, -16.3, 0.0) | 7 | 0.2 | 1.8 | 0.12 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
