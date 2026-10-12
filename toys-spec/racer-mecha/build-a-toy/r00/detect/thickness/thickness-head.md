# Thickness and hollow

`part_head.step.py --nozzle 0.4 --min-wall 3.0 --report /home/loginuserxx/harnesses/worktrees/autonomous-workshop/noble-lagoon-2/toys-spec/racer-mecha/build-a-toy/r00/detect/thickness/thickness-head.md`

part_head.step.py: 6.01 cm3 solid, grid 0.500 mm (43x113x37), 9652 surface samples, thickness resolved to 0.250 mm

| check | status | detail |
|---|---|---|
| wall >= 3.00 mm (+/-0.25) | FAIL | 26.8% of surface below (2832 of 9652 samples); thinnest 1.50 mm at (7.0, 16.5, 15.2) in 4 region(s); 2 wall(s) (widest band 15.69 mm), 2 taper(s) at feature edges (1.04% of surface, budget 2%) |
| thickness distribution | PASS | median 9.75 mm, p95 21.00 mm, max 53.50 mm |
| hollowable at 1.20 mm wall | WARN | 3.19 of 6.01 cm3 (53%) in 1 pocket(s) |
| filament that would save | PASS | 0.48 cm3, 0.6 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

`feature` is the print-details feature the region lies on, else the nearest B-rep face; `under limit` is how far its thinnest point is below the 3.00 mm wall.

| # | kind | thinnest | under limit | at | feature | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|---|---|
| 1 | wall | 2.00 mm | 1.00 mm | (-4.0, -1.5, 1.1) | face 33 (plane, 280.0 mm2, centre (-4.0, -9.5, 4.0); no print-details feature within 1 mm), 0.00 mm away | 1390 | 408.2 | 26.0 | 15.69 |
| 2 | wall | 2.25 mm | 0.75 mm | (4.0, -17.5, 5.2) | face 31 (plane, 280.0 mm2, centre (4.0, -9.5, 4.0); no print-details feature within 1 mm), 0.00 mm away | 1376 | 406.8 | 26.1 | 15.60 |
| 3 | taper | 1.50 mm | 1.50 mm | (7.0, 16.5, 15.2) | face 13 (plane, 15.0 mm2, centre (7.0, 13.0, 14.5); no print-details feature within 1 mm), 0.00 mm away | 27 | 16.8 | 8.8 | 1.91 |
| 4 | taper | 1.75 mm | 1.25 mm | (-7.0, 8.6, 15.2) | face 10 (plane, 15.0 mm2, centre (-7.0, 13.0, 14.5); no print-details feature within 1 mm), 0.00 mm away | 39 | 16.0 | 9.3 | 1.72 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
