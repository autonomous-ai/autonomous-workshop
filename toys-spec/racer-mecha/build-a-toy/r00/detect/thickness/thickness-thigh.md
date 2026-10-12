# Thickness and hollow

`part_thigh.step.py --nozzle 0.4 --min-wall 3.0 --report /home/loginuserxx/harnesses/worktrees/autonomous-workshop/noble-lagoon-2/toys-spec/racer-mecha/build-a-toy/r00/detect/thickness/thickness-thigh.md`

part_thigh.step.py: 6.20 cm3 solid, grid 0.500 mm (55x49x61), 11529 surface samples, thickness resolved to 0.250 mm

| check | status | detail |
|---|---|---|
| wall >= 3.00 mm (+/-0.25) | FAIL | 9.8% of surface below (1238 of 11529 samples); thinnest 1.00 mm at (23.7, -2.0, 15.3) in 5 region(s); 3 wall(s) (widest band 16.55 mm), 2 taper(s) at feature edges (0.69% of surface, budget 2%); 582 more within measurement error of the limit |
| thickness distribution | PASS | median 7.00 mm, p95 24.75 mm, max 27.50 mm |
| hollowable at 1.20 mm wall | WARN | 2.90 of 6.20 cm3 (47%) in 1 pocket(s) |
| filament that would save | PASS | 0.43 cm3, 0.5 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

`feature` is the print-details feature the region lies on, else the nearest B-rep face; `under limit` is how far its thinnest point is below the 3.00 mm wall.

| # | kind | thinnest | under limit | at | feature | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|---|---|
| 1 | wall | 1.00 mm | 2.00 mm | (13.1, -1.9, 28.2) | face 35 (cylinder, 116.2 mm2, centre (9.0, -2.0, 26.4); no print-details feature within 1 mm), 0.00 mm away | 826 | 214.8 | 13.0 | 16.55 |
| 2 | wall | 1.25 mm | 1.75 mm | (6.1, -2.2, 1.6) | face 6 (cylinder, 45.4 mm2, centre (4.0, -2.0, 2.7); no print-details feature within 1 mm), 0.00 mm away | 245 | 63.0 | 8.5 | 7.39 |
| 3 | wall | 1.25 mm | 1.75 mm | (23.3, -2.1, 1.6) | face 28 (cylinder, 19.4 mm2, centre (24.0, -2.0, 2.7); no print-details feature within 1 mm), 0.00 mm away | 87 | 26.2 | 6.0 | 4.34 |
| 4 | taper | 1.00 mm | 2.00 mm | (23.7, -2.0, 15.3) | face 21 (plane, 42.0 mm2, centre (23.7, -2.0, 16.0); no print-details feature within 1 mm), 0.00 mm away | 56 | 16.0 | 9.4 | 1.70 |
| 5 | taper | 1.50 mm | 1.50 mm | (8.2, 5.5, 7.0) | face 3 (plane, 238.1 mm2, centre (13.0, 4.5, 5.8); no print-details feature within 1 mm), 0.00 mm away | 24 | 7.1 | 14.5 | 0.49 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
