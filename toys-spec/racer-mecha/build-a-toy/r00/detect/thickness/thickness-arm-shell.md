# Thickness and hollow

`part_arm-shell.step.py --nozzle 0.4 --min-wall 2.5 --report /home/loginuserxx/harnesses/worktrees/autonomous-workshop/noble-lagoon-2/toys-spec/racer-mecha/build-a-toy/r00/detect/thickness/thickness-arm-shell.md`

part_arm-shell.step.py: 8.64 cm3 solid, grid 0.417 mm (53x113x58), 28529 surface samples, thickness resolved to 0.208 mm

| check | status | detail |
|---|---|---|
| wall >= 2.50 mm (+/-0.21) | PASS | 0.0% of surface below (2 of 28529 samples); thinnest 0.62 mm at (10.0, 4.6, 0.5) in 1 region(s); no region is a wall, 1 taper(s) at feature edges (0.01% of surface, budget 2%); 6709 more within measurement error of the limit |
| thickness distribution | PASS | median 2.92 mm, p95 22.08 mm, max 45.00 mm |
| hollowable at 1.20 mm wall | WARN | 2.07 of 8.64 cm3 (24%) in 7 pocket(s) |
| filament that would save | PASS | 0.31 cm3, 0.4 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

`feature` is the print-details feature the region lies on, else the nearest B-rep face; `under limit` is how far its thinnest point is below the 2.50 mm wall.

| # | kind | thinnest | under limit | at | feature | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|---|---|
| 1 | taper | 0.62 mm | 1.88 mm | (10.0, 4.6, 0.5) | face 51 (plane, 899.7 mm2, centre (10.0, -0.0, 11.0); no print-details feature within 1 mm), 0.00 mm away | 2 | 0.4 | 0.2 | 0.88 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
