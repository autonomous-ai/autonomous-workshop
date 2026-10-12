# Thickness and hollow

`part_nose.step.py --nozzle 0.4 --min-wall 0.9 --report /home/loginuserxx/harnesses/worktrees/autonomous-workshop/noble-lagoon-2/toys-spec/racer-mecha/build-a-toy/r00/detect/thickness19/thickness-nose.md`

part_nose.step.py: 20.61 cm3 solid, grid 0.211 mm (260x111x405), 175279 surface samples, thickness resolved to 0.106 mm

| check | status | detail |
|---|---|---|
| wall >= 0.90 mm (+/-0.11) | PASS | 0.0% of surface below (45 of 175279 samples); thinnest 0.42 mm at (-4.5, -31.5, 60.2) in 6 region(s); no region is a wall, 5 taper(s) at feature edges and 1 spot(s) too small to be a wall (0.03% of surface, budget 2%); 13 more within measurement error of the limit |
| thickness distribution | PASS | median 10.34 mm, p95 53.82 mm, max 84.43 mm |
| hollowable at 1.20 mm wall | WARN | 11.29 of 20.61 cm3 (55%) in 2 pocket(s), 1 too small to shell |
| filament that would save | PASS | 1.69 cm3, 2.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

`feature` is the print-details feature the region lies on, else the nearest B-rep face; `under limit` is how far its thinnest point is below the 0.90 mm wall.

| # | kind | thinnest | under limit | at | feature | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|---|---|
| 1 | taper | 0.42 mm | 0.48 mm | (-7.1, -14.1, 75.5) | face 54 (plane, 80.9 mm2, centre (0.0, -15.4, 77.1); no print-details feature within 1 mm), 0.00 mm away | 17 | 0.8 | 4.2 | 0.20 |
| 2 | taper | 0.42 mm | 0.48 mm | (3.0, -14.1, 75.5) | face 54 (plane, 80.9 mm2, centre (0.0, -15.4, 77.1); no print-details feature within 1 mm), 0.00 mm away | 11 | 0.5 | 5.1 | 0.11 |
| 3 | taper | 0.42 mm | 0.48 mm | (-3.6, -31.5, 60.2) | face 46 (plane, 5.2 mm2, centre (-0.0, -31.4, 60.2); no print-details feature within 1 mm), 0.00 mm away | 3 | 0.4 | 1.2 | 0.33 |
| 4 | taper | 0.42 mm | 0.48 mm | (-2.1, -14.1, 75.5) | face 54 (plane, 80.9 mm2, centre (0.0, -15.4, 77.1); no print-details feature within 1 mm), 0.00 mm away | 7 | 0.3 | 1.3 | 0.26 |
| 5 | spot | 0.42 mm | 0.48 mm | (-4.5, -31.5, 60.2) | face 46 (plane, 5.2 mm2, centre (-0.0, -31.4, 60.2); no print-details feature within 1 mm), 0.00 mm away | 2 | 0.3 | 0.3 | 0.99 |
| 6 | taper | 0.42 mm | 0.48 mm | (8.5, -14.1, 75.5) | face 54 (plane, 80.9 mm2, centre (0.0, -15.4, 77.1); no print-details feature within 1 mm), 0.00 mm away | 5 | 0.2 | 1.1 | 0.22 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
