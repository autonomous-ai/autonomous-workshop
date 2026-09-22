# Thickness and hollow

`part_sun_orange.step.py --nozzle 0.4 --report measure/thickness-sun_orange.md`

part_sun_orange.step.py: 92.12 cm3 solid, grid 0.291 mm (646x652x26), 356298 surface samples, thickness resolved to 0.146 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.15) | PASS | 0.0% of surface below (65 of 356298 samples); thinnest 0.29 mm at (-36.1, 73.6, 5.0) in 48 region(s); no region is a wall, 46 taper(s) at feature edges and 2 spot(s) too small to be a wall (0.02% of surface, budget 2%); 173 more within measurement error of the limit |
| thickness distribution | PASS | median 3.78 mm, p95 11.64 mm, max 179.14 mm |
| hollowable at 1.20 mm wall | WARN | 34.24 of 92.12 cm3 (37%) in 1 pocket(s), 42 too small to shell |
| filament that would save | PASS | 5.14 cm3, 6.4 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.58 mm | (-10.4, 26.1, 5.4) | 5 | 0.7 | 3.0 | 0.23 |
| 2 | taper | 0.58 mm | (21.5, -16.9, 5.4) | 4 | 0.5 | 1.2 | 0.47 |
| 3 | taper | 0.58 mm | (11.0, 25.7, 5.4) | 3 | 0.4 | 1.1 | 0.37 |
| 4 | taper | 0.58 mm | (-28.1, -3.3, 5.4) | 2 | 0.3 | 2.0 | 0.14 |
| 5 | taper | 0.58 mm | (27.6, -11.8, 5.4) | 2 | 0.3 | 1.5 | 0.19 |
| 6 | spot | 0.58 mm | (24.6, 10.6, 5.4) | 2 | 0.3 | 0.0 | 0.96 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
