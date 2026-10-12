# Thickness and hollow

`part_nose.step.py --nozzle 0.4 --min-wall 2.0 --report /home/loginuserxx/harnesses/worktrees/autonomous-workshop/noble-lagoon-2/toys-spec/racer-mecha/build-a-toy/r00/detect/thickness/thickness-nose.md`

part_nose.step.py: 20.79 cm3 solid, grid 0.333 mm (167x72x258), 67487 surface samples, thickness resolved to 0.167 mm

| check | status | detail |
|---|---|---|
| wall >= 2.00 mm (+/-0.17) | FAIL | 1.2% of surface below (823 of 67487 samples); thinnest 0.33 mm at (8.4, -14.1, 75.4) in 2 region(s); 1 wall(s) (widest band 4.60 mm), 1 taper(s) at feature edges (0.12% of surface, budget 2%); 1770 more within measurement error of the limit |
| thickness distribution | PASS | median 10.33 mm, p95 53.83 mm, max 84.33 mm |
| hollowable at 1.20 mm wall | WARN | 11.17 of 20.79 cm3 (54%) in 2 pocket(s), 2 too small to shell |
| filament that would save | PASS | 1.68 cm3, 2.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

`feature` is the print-details feature the region lies on, else the nearest B-rep face; `under limit` is how far its thinnest point is below the 2.00 mm wall.

| # | kind | thinnest | under limit | at | feature | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|---|---|
| 1 | wall | 1.00 mm | 1.00 mm | (7.5, -14.2, 84.5) | face 51 (plane, 335.2 mm2, centre (0.0, -23.5, 84.5); no print-details feature within 1 mm), 0.00 mm away | 748 | 88.1 | 19.1 | 4.60 |
| 2 | taper | 0.33 mm | 1.67 mm | (8.4, -14.1, 75.4) | face 54 (plane, 80.9 mm2, centre (0.0, -15.4, 77.1); no print-details feature within 1 mm), 0.00 mm away | 75 | 9.9 | 17.0 | 0.58 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
