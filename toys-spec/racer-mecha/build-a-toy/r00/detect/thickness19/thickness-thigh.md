# Thickness and hollow

`part_thigh.step.py --nozzle 0.4 --min-wall 1.4 --report /home/loginuserxx/harnesses/worktrees/autonomous-workshop/noble-lagoon-2/toys-spec/racer-mecha/build-a-toy/r00/detect/thickness19/thickness-thigh.md`

part_thigh.step.py: 6.16 cm3 solid, grid 0.233 mm (112x99x126), 57086 surface samples, thickness resolved to 0.117 mm

| check | status | detail |
|---|---|---|
| wall >= 1.40 mm (+/-0.12) | PASS | 0.2% of surface below (99 of 57086 samples); thinnest 0.23 mm at (7.6, 5.3, 6.7) in 3 region(s); no region is a wall, 3 taper(s) at feature edges (0.17% of surface, budget 2%); 164 more within measurement error of the limit |
| thickness distribution | PASS | median 7.23 mm, p95 24.85 mm, max 27.77 mm |
| hollowable at 1.20 mm wall | WARN | 2.67 of 6.16 cm3 (43%) in 1 pocket(s) |
| filament that would save | PASS | 0.40 cm3, 0.5 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

`feature` is the print-details feature the region lies on, else the nearest B-rep face; `under limit` is how far its thinnest point is below the 1.40 mm wall.

| # | kind | thinnest | under limit | at | feature | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|---|---|
| 1 | taper | 0.23 mm | 1.17 mm | (7.6, 5.3, 6.7) | face 3 (plane, 238.1 mm2, centre (13.0, 4.5, 5.8); no print-details feature within 1 mm), 0.00 mm away | 61 | 3.6 | 14.9 | 0.24 |
| 2 | taper | 1.17 mm | 0.23 mm | (23.7, -2.2, 15.2) | face 21 (plane, 42.0 mm2, centre (23.7, -2.0, 16.0); no print-details feature within 1 mm), 0.00 mm away | 20 | 1.3 | 1.5 | 0.84 |
| 3 | taper | 1.17 mm | 0.23 mm | (22.5, -2.0, 15.3) | face 11 (plane, 131.9 mm2, centre (22.5, -1.7, 7.9); no print-details feature within 1 mm), 0.00 mm away | 18 | 1.0 | 1.4 | 0.74 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
