# Thickness and hollow

`part_head.step.py --nozzle 0.4 --min-wall 1.9 --report /home/loginuserxx/harnesses/worktrees/autonomous-workshop/noble-lagoon-2/toys-spec/racer-mecha/build-a-toy/r00/detect/thickness19/thickness-head.md`

part_head.step.py: 5.95 cm3 solid, grid 0.317 mm (65x175x55), 26604 surface samples, thickness resolved to 0.158 mm

| check | status | detail |
|---|---|---|
| wall >= 1.90 mm (+/-0.16) | PASS | 0.0% of surface below (4 of 26604 samples); thinnest 1.42 mm at (-7.0, 8.5, 15.3) in 3 region(s); no region is a wall, 3 taper(s) at feature edges (0.03% of surface, budget 2%); 49 more within measurement error of the limit |
| thickness distribution | PASS | median 9.97 mm, p95 21.22 mm, max 53.52 mm |
| hollowable at 1.20 mm wall | WARN | 2.78 of 5.95 cm3 (47%) in 2 pocket(s) |
| filament that would save | PASS | 0.42 cm3, 0.5 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

`feature` is the print-details feature the region lies on, else the nearest B-rep face; `under limit` is how far its thinnest point is below the 1.90 mm wall.

| # | kind | thinnest | under limit | at | feature | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|---|---|
| 1 | taper | 1.58 mm | 0.32 mm | (7.0, 8.5, 15.3) | face 13 (plane, 15.0 mm2, centre (7.0, 13.0, 14.5); no print-details feature within 1 mm), 0.00 mm away | 2 | 0.5 | 0.3 | 1.55 |
| 2 | taper | 1.42 mm | 0.48 mm | (-7.0, 8.5, 15.3) | face 10 (plane, 15.0 mm2, centre (-7.0, 13.0, 14.5); no print-details feature within 1 mm), 0.00 mm away | 1 | 0.3 | 0.0 | 0.88 |
| 3 | taper | 1.58 mm | 0.32 mm | (7.0, 17.1, 15.3) | face 13 (plane, 15.0 mm2, centre (7.0, 13.0, 14.5); no print-details feature within 1 mm), 0.00 mm away | 1 | 0.1 | 0.0 | 0.33 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
