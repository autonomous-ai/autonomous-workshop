# Thickness and hollow

`part_spine.step.py --nozzle 0.4 --min-wall 3.0 --report /home/loginuserxx/harnesses/worktrees/autonomous-workshop/noble-lagoon-2/toys-spec/racer-mecha/build-a-toy/r00/detect/thickness/thickness-spine.md`

part_spine.step.py: 39.55 cm3 solid, grid 0.500 mm (171x43x249), 46988 surface samples, thickness resolved to 0.250 mm

| check | status | detail |
|---|---|---|
| wall >= 3.00 mm (+/-0.25) | PASS | 0.2% of surface below (22 of 46988 samples); thinnest 1.00 mm at (-5.0, 20.3, 107.7) in 2 region(s); no region is a wall, 2 taper(s) at feature edges (0.16% of surface, budget 2%); 5 more within measurement error of the limit |
| thickness distribution | PASS | median 13.50 mm, p95 22.41 mm, max 121.50 mm |
| hollowable at 1.20 mm wall | WARN | 27.40 of 39.55 cm3 (69%) in 1 pocket(s) |
| filament that would save | PASS | 4.11 cm3, 5.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

`feature` is the print-details feature the region lies on, else the nearest B-rep face; `under limit` is how far its thinnest point is below the 3.00 mm wall.

| # | kind | thinnest | under limit | at | feature | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|---|---|
| 1 | taper | 1.25 mm | 1.75 mm | (-4.1, 20.1, 101.2) | face 93 (plane, 24.9 mm2, centre (-4.4, 20.8, 103.5); no print-details feature within 1 mm), 0.00 mm away | 11 | 11.6 | 9.7 | 1.20 |
| 2 | taper | 1.00 mm | 2.00 mm | (-5.0, 20.3, 107.7) | face 93 (plane, 24.9 mm2, centre (-4.4, 20.8, 103.5); no print-details feature within 1 mm), 0.00 mm away | 11 | 7.8 | 10.0 | 0.78 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
