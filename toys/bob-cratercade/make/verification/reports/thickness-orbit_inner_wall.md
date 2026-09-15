# Thickness and hollow

`part_orbit_inner_wall.step.py --nozzle 0.4 --report measure/thickness-orbit_inner_wall.md`

part_orbit_inner_wall.step.py: 7.54 cm3 solid, grid 0.147 mm (316x209x168), 210437 surface samples, thickness resolved to 0.074 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (10 of 210437 samples); thinnest 0.15 mm at (3.8, 12.6, 0.7) in 2 region(s); no region is a wall, 2 taper(s) at feature edges (0.00% of surface, budget 2%) |
| thickness distribution | PASS | median 3.97 mm, p95 23.96 mm, max 23.96 mm |
| hollowable at 1.20 mm wall | WARN | 2.47 of 7.54 cm3 (33%) in 1 pocket(s) |
| filament that would save | PASS | 0.37 cm3, 0.5 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.15 mm | (3.8, 12.6, 0.7) | 8 | 0.2 | 1.2 | 0.14 |
| 2 | taper | 0.22 mm | (0.0, 13.9, 23.2) | 2 | 0.0 | 0.1 | 0.30 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
