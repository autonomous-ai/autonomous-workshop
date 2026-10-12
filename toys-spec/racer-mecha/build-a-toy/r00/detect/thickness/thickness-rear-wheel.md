# Thickness and hollow

`part_rear-wheel.step.py --nozzle 0.4 --min-wall 2.0 --report /home/loginuserxx/harnesses/worktrees/autonomous-workshop/noble-lagoon-2/toys-spec/racer-mecha/build-a-toy/r00/detect/thickness/thickness-rear-wheel.md`

part_rear-wheel.step.py: 7.83 cm3 solid, grid 0.333 mm (107x107x41), 30948 surface samples, thickness resolved to 0.167 mm

| check | status | detail |
|---|---|---|
| wall >= 2.00 mm (+/-0.17) | PASS | 0.0% of surface below (3 of 30948 samples); thinnest 0.50 mm at (4.9, 4.0, 3.4) in 3 region(s); no region is a wall, 3 taper(s) at feature edges (0.01% of surface, budget 2%) |
| thickness distribution | PASS | median 6.83 mm, p95 12.33 mm, max 16.83 mm |
| hollowable at 1.20 mm wall | WARN | 3.56 of 7.83 cm3 (45%) in 2 pocket(s) |
| filament that would save | PASS | 0.53 cm3, 0.7 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

`feature` is the print-details feature the region lies on, else the nearest B-rep face; `under limit` is how far its thinnest point is below the 2.00 mm wall.

| # | kind | thinnest | under limit | at | feature | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|---|---|
| 1 | taper | 1.33 mm | 0.67 mm | (-8.6, 0.4, 3.0) | face 21 (plane, 14.0 mm2, centre (-7.8, 0.2, 4.0); no print-details feature within 1 mm), 0.00 mm away | 1 | 0.1 | 0.0 | 0.37 |
| 2 | taper | 0.50 mm | 1.50 mm | (4.9, 4.0, 3.4) | face 29 (plane, 14.0 mm2, centre (6.4, 4.5, 4.0); no print-details feature within 1 mm), 0.00 mm away | 1 | 0.1 | 0.0 | 0.33 |
| 3 | taper | 1.50 mm | 0.50 mm | (2.9, -7.8, 3.4) | face 15 (plane, 14.0 mm2, centre (2.6, -7.4, 4.0); no print-details feature within 1 mm), 0.00 mm away | 1 | 0.1 | 0.0 | 0.24 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
