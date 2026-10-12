# Thickness and hollow

`part_torso.step.py --nozzle 0.4 --min-wall 3.0 --report /home/loginuserxx/harnesses/worktrees/autonomous-workshop/noble-lagoon-2/toys-spec/racer-mecha/build-a-toy/r00/detect/thickness/thickness-torso.md`

part_torso.step.py: 117.45 cm3 solid, grid 0.500 mm (127x95x191), 88429 surface samples, thickness resolved to 0.250 mm

| check | status | detail |
|---|---|---|
| wall >= 3.00 mm (+/-0.25) | FAIL | 3.5% of surface below (3206 of 88429 samples); thinnest 0.75 mm at (0.5, -1.0, 2.7) in 12 region(s); 8 wall(s) (widest band 17.35 mm), 4 taper(s) at feature edges (0.13% of surface, budget 2%); 1215 more within measurement error of the limit |
| thickness distribution | PASS | median 24.50 mm, p95 81.00 mm, max 93.00 mm |
| hollowable at 1.20 mm wall | WARN | 91.91 of 117.45 cm3 (78%) in 1 pocket(s) |
| filament that would save | PASS | 13.79 cm3, 17.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

`feature` is the print-details feature the region lies on, else the nearest B-rep face; `under limit` is how far its thinnest point is below the 3.00 mm wall.

| # | kind | thinnest | under limit | at | feature | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|---|---|
| 1 | wall | 1.75 mm | 1.25 mm | (4.4, 10.0, 42.5) | face 154 (plane, 194.3 mm2, centre (0.0, 10.0, 34.8); no print-details feature within 1 mm), 0.00 mm away | 1245 | 358.5 | 20.7 | 17.35 |
| 2 | wall | 1.25 mm | 1.75 mm | (27.1, -2.5, 1.5) | face 128 (cylinder, 61.5 mm2, centre (24.7, -2.0, 2.7); no print-details feature within 1 mm), 0.00 mm away | 326 | 85.8 | 14.0 | 6.15 |
| 3 | wall | 1.25 mm | 1.75 mm | (-12.6, -12.9, 84.3) | face 113 (cylinder, 53.3 mm2, centre (-11.5, -14.0, 81.7); no print-details feature within 1 mm), 0.00 mm away | 309 | 85.6 | 10.2 | 8.38 |
| 4 | wall | 1.25 mm | 1.75 mm | (12.0, -12.9, 84.3) | face 121 (cylinder, 53.3 mm2, centre (11.5, -14.0, 81.7); no print-details feature within 1 mm), 0.00 mm away | 303 | 84.4 | 10.2 | 8.26 |
| 5 | wall | 1.25 mm | 1.75 mm | (-28.1, -2.4, 1.5) | face 17 (cylinder, 61.5 mm2, centre (-24.7, -2.0, 2.7); no print-details feature within 1 mm), 0.00 mm away | 311 | 80.2 | 13.9 | 5.78 |
| 6 | wall | 1.75 mm | 1.25 mm | (28.7, -0.3, 93.0) | face 85 (plane, 338.0 mm2, centre (22.5, 0.0, 93.0); no print-details feature within 1 mm), 0.00 mm away | 218 | 56.9 | 17.8 | 3.20 |
| 7 | wall | 1.75 mm | 1.25 mm | (-28.6, -0.3, 93.0) | face 12 (plane, 338.0 mm2, centre (-22.5, 0.0, 93.0); no print-details feature within 1 mm), 0.00 mm away | 210 | 55.7 | 15.8 | 3.52 |
| 8 | wall | 0.75 mm | 2.25 mm | (0.5, -1.0, 2.7) | face 198 (plane, 7.4 mm2, centre (0.5, -2.0, 3.5); no print-details feature within 1 mm), 0.00 mm away | 166 | 40.3 | 7.9 | 5.12 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
