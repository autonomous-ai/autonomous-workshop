# Thickness and hollow

`part_forearm.step.py --nozzle 0.4 --min-wall 3.0 --report /home/loginuserxx/harnesses/worktrees/autonomous-workshop/noble-lagoon-2/toys-spec/racer-mecha/build-a-toy/r00/detect/thickness/thickness-forearm.md`

part_forearm.step.py: 6.75 cm3 solid, grid 0.500 mm (74x35x33), 8288 surface samples, thickness resolved to 0.250 mm

| check | status | detail |
|---|---|---|
| wall >= 3.00 mm (+/-0.25) | PASS | 0.2% of surface below (16 of 8288 samples); thinnest 1.25 mm at (28.0, -8.9, 5.9) in 4 region(s); no region is a wall, 4 taper(s) at feature edges (0.22% of surface, budget 2%); 1 more within measurement error of the limit |
| thickness distribution | PASS | median 14.00 mm, p95 32.00 mm, max 34.00 mm |
| hollowable at 1.20 mm wall | WARN | 4.43 of 6.75 cm3 (66%) in 1 pocket(s) |
| filament that would save | PASS | 0.66 cm3, 0.8 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

`feature` is the print-details feature the region lies on, else the nearest B-rep face; `under limit` is how far its thinnest point is below the 3.00 mm wall.

| # | kind | thinnest | under limit | at | feature | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|---|---|
| 1 | taper | 2.50 mm | 0.50 mm | (0.0, -9.1, 4.1) | face 2 (plane, 209.0 mm2, centre (0.0, -2.0, 7.0); no print-details feature within 1 mm), 0.00 mm away | 9 | 3.2 | 3.8 | 0.84 |
| 2 | taper | 2.50 mm | 0.50 mm | (0.0, -9.0, 12.3) | face 2 (plane, 209.0 mm2, centre (0.0, -2.0, 7.0); no print-details feature within 1 mm), 0.00 mm away | 5 | 1.6 | 2.1 | 0.75 |
| 3 | taper | 2.50 mm | 0.50 mm | (0.0, -9.0, 8.4) | face 2 (plane, 209.0 mm2, centre (0.0, -2.0, 7.0); no print-details feature within 1 mm), 0.00 mm away | 1 | 0.2 | 0.0 | 0.50 |
| 4 | taper | 1.25 mm | 1.75 mm | (28.0, -8.9, 5.9) | face 57 (cylinder, 4.3 mm2, centre (27.0, -9.1, 6.4); no print-details feature within 1 mm), 0.00 mm away | 1 | 0.0 | 0.0 | 0.07 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
