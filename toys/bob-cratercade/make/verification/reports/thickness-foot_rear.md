# Thickness and hollow

`part_foot_rear.step.py --nozzle 0.4 --report measure/thickness-foot_rear.md`

part_foot_rear.step.py: 31.38 cm3 solid, grid 0.239 mm (230x138x359), 301304 surface samples, thickness resolved to 0.120 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.12) | PASS | 0.0% of surface below (7 of 301304 samples); thinnest 0.48 mm at (25.8, -16.0, 84.6) in 2 region(s); no region is a wall, 2 taper(s) at feature edges (0.00% of surface, budget 2%); 84 more within measurement error of the limit |
| thickness distribution | PASS | median 2.99 mm, p95 31.85 mm, max 84.29 mm |
| hollowable at 1.20 mm wall | WARN | 11.25 of 31.38 cm3 (36%) in 1 pocket(s) |
| filament that would save | PASS | 1.69 cm3, 2.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.48 mm | (-26.2, -16.0, 84.7) | 5 | 0.3 | 0.7 | 0.45 |
| 2 | taper | 0.48 mm | (25.8, -16.0, 84.6) | 2 | 0.1 | 0.1 | 0.56 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
