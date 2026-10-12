# Thickness and hollow

`part_shin.step.py --nozzle 0.4 --min-wall 3.0 --report /home/loginuserxx/harnesses/worktrees/autonomous-workshop/noble-lagoon-2/toys-spec/racer-mecha/build-a-toy/r00/detect/thickness/thickness-shin.md`

part_shin.step.py: 49.57 cm3 solid, grid 0.500 mm (67x61x174), 35078 surface samples, thickness resolved to 0.250 mm

| check | status | detail |
|---|---|---|
| wall >= 3.00 mm (+/-0.25) | FAIL | 3.1% of surface below (1131 of 35078 samples); thinnest 1.25 mm at (23.6, -12.7, 48.2) in 9 region(s); 1 wall(s) (widest band 18.71 mm), 8 taper(s) at feature edges (0.01% of surface, budget 2%); 68 more within measurement error of the limit |
| thickness distribution | PASS | median 22.75 mm, p95 75.75 mm, max 84.00 mm |
| hollowable at 1.20 mm wall | WARN | 39.86 of 49.57 cm3 (80%) in 1 pocket(s) |
| filament that would save | PASS | 5.98 cm3, 7.4 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

`feature` is the print-details feature the region lies on, else the nearest B-rep face; `under limit` is how far its thinnest point is below the 3.00 mm wall.

| # | kind | thinnest | under limit | at | feature | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|---|---|
| 1 | wall | 1.25 mm | 1.75 mm | (12.3, -1.9, 84.5) | face 84 (cylinder, 175.9 mm2, centre (15.0, -2.0, 82.5); no print-details feature within 1 mm), 0.00 mm away | 1117 | 299.8 | 16.0 | 18.71 |
| 2 | taper | 2.50 mm | 0.50 mm | (10.3, -12.5, 39.8) | slit-5 (part_shin.step.py:106), 0.00 mm away | 2 | 0.1 | 0.4 | 0.21 |
| 3 | taper | 1.25 mm | 1.75 mm | (23.6, -12.7, 48.2) | slit-3 (part_shin.step.py:98), 0.00 mm away | 2 | 0.1 | 0.4 | 0.21 |
| 4 | taper | 1.75 mm | 1.25 mm | (28.4, -12.6, 48.0) | slit-3 (part_shin.step.py:98), 0.00 mm away | 2 | 0.1 | 0.3 | 0.21 |
| 5 | taper | 1.75 mm | 1.25 mm | (28.4, -12.6, 62.1) | slit-4 (part_shin.step.py:98), 0.00 mm away | 2 | 0.1 | 0.3 | 0.21 |
| 6 | taper | 1.25 mm | 1.75 mm | (4.1, -12.7, 13.6) | slit-9 (part_shin.step.py:129), 0.00 mm away | 2 | 0.1 | 0.3 | 0.21 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
