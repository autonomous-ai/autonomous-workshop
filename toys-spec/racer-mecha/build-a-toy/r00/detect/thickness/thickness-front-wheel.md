# Thickness and hollow

`part_front-wheel.step.py --nozzle 0.4 --min-wall 2.0 --report /home/loginuserxx/harnesses/worktrees/autonomous-workshop/noble-lagoon-2/toys-spec/racer-mecha/build-a-toy/r00/detect/thickness/thickness-front-wheel.md`

part_front-wheel.step.py: 12.06 cm3 solid, grid 0.333 mm (119x119x53), 47771 surface samples, thickness resolved to 0.167 mm

| check | status | detail |
|---|---|---|
| wall >= 2.00 mm (+/-0.17) | PASS | 1.6% of surface below (404 of 47771 samples); thinnest 0.33 mm at (-8.9, 12.0, 0.6) in 13 region(s); no region is a wall, 12 taper(s) at feature edges and 1 spot(s) too small to be a wall (1.57% of surface, budget 2%); 94 more within measurement error of the limit |
| thickness distribution | PASS | median 6.00 mm, p95 17.17 mm, max 21.83 mm |
| hollowable at 1.20 mm wall | WARN | 5.62 of 12.06 cm3 (47%) in 1 pocket(s) |
| filament that would save | PASS | 0.84 cm3, 1.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

`feature` is the print-details feature the region lies on, else the nearest B-rep face; `under limit` is how far its thinnest point is below the 2.00 mm wall.

| # | kind | thinnest | under limit | at | feature | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|---|---|
| 1 | taper | 0.33 mm | 1.67 mm | (-0.3, -5.9, 0.4) | face 58 (cylinder, 11.9 mm2, centre (-0.7, -5.6, 4.2); no print-details feature within 1 mm), 0.00 mm away | 133 | 30.5 | 32.3 | 0.94 |
| 2 | taper | 0.33 mm | 1.67 mm | (-8.9, 12.0, 0.6) | face 1 (cone, 57.8 mm2, centre (0.0, 0.0, 0.8); no print-details feature within 1 mm), 0.01 mm away | 76 | 18.3 | 19.1 | 0.96 |
| 3 | taper | 0.33 mm | 1.67 mm | (4.2, 14.1, 0.7) | face 0 (cone, 283.7 mm2, centre (0.0, 0.0, 1.8); no print-details feature within 1 mm), 0.01 mm away | 64 | 14.9 | 15.3 | 0.98 |
| 4 | taper | 0.33 mm | 1.67 mm | (-5.1, -2.6, 0.2) | face 71 (cone, 3.7 mm2, centre (-4.3, -3.1, 0.4); no print-details feature within 1 mm), 0.00 mm away | 71 | 14.9 | 15.1 | 0.99 |
| 5 | taper | 1.00 mm | 1.00 mm | (11.3, 0.6, 0.3) | face 43 (plane, 5.5 mm2, centre (9.1, 0.7, 0.4); no print-details feature within 1 mm), 0.00 mm away | 30 | 6.5 | 7.1 | 0.92 |
| 6 | taper | 0.83 mm | 1.17 mm | (5.7, 2.1, 0.4) | face 33 (cylinder, 11.9 mm2, centre (5.1, 2.4, 4.2); no print-details feature within 1 mm), 0.00 mm away | 13 | 2.8 | 5.1 | 0.54 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
