# Thickness and hollow

`part_shin.step.py --nozzle 0.4 --min-wall 1.9 --report /home/loginuserxx/harnesses/worktrees/autonomous-workshop/noble-lagoon-2/toys-spec/racer-mecha/build-a-toy/r00/detect/thickness19/thickness-shin.md`

part_shin.step.py: 49.24 cm3 solid, grid 0.317 mm (103x93x272), 91165 surface samples, thickness resolved to 0.158 mm

| check | status | detail |
|---|---|---|
| wall >= 1.90 mm (+/-0.16) | PASS | 0.1% of surface below (124 of 91165 samples); thinnest 1.42 mm at (30.0, -12.7, 62.2) in 6 region(s); no region is a wall, 6 taper(s) at feature edges (0.12% of surface, budget 2%); 291 more within measurement error of the limit |
| thickness distribution | PASS | median 22.80 mm, p95 75.84 mm, max 84.23 mm |
| hollowable at 1.20 mm wall | WARN | 37.55 of 49.24 cm3 (76%) in 1 pocket(s) |
| filament that would save | PASS | 5.63 cm3, 7.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

`feature` is the print-details feature the region lies on, else the nearest B-rep face; `under limit` is how far its thinnest point is below the 1.90 mm wall.

| # | kind | thinnest | under limit | at | feature | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|---|---|
| 1 | taper | 1.42 mm | 0.48 mm | (11.0, -2.0, 84.5) | face 84 (cylinder, 175.9 mm2, centre (15.0, -2.0, 82.5); no print-details feature within 1 mm), 0.00 mm away | 111 | 11.4 | 13.4 | 0.85 |
| 2 | taper | 1.42 mm | 0.48 mm | (30.0, -12.7, 62.2) | face 0 (plane, 982.6 mm2, centre (30.0, -2.0, 49.5); no print-details feature within 1 mm), 0.00 mm away | 4 | 0.3 | 1.9 | 0.17 |
| 3 | taper | 1.58 mm | 0.32 mm | (2.5, -12.7, 13.7) | face 45 (plane, 537.7 mm2, centre (2.5, -2.0, 12.2); no print-details feature within 1 mm), 0.00 mm away | 4 | 0.3 | 1.7 | 0.19 |
| 4 | taper | 1.42 mm | 0.48 mm | (23.6, -12.7, 62.1) | slit-4 (part_shin.step.py:98), 0.00 mm away | 2 | 0.1 | 0.1 | 0.33 |
| 5 | taper | 1.58 mm | 0.32 mm | (28.4, -12.7, 48.1) | slit-3 (part_shin.step.py:98), 0.00 mm away | 2 | 0.1 | 0.2 | 0.33 |
| 6 | taper | 1.42 mm | 0.48 mm | (23.6, -12.8, 48.6) | slit-3 (part_shin.step.py:98), 0.00 mm away | 1 | 0.1 | 0.0 | 0.20 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
