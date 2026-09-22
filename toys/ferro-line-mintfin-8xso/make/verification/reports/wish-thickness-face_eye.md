# Thickness and hollow

`artifacts/make/r0001/product/mintfin/part_face_eye.step.py --nozzle .4 --min-wall 1.2 --report artifacts/make/r0001/product/mintfin/measure/wish-thickness-face_eye.md`

part_face_eye.step.py: 0.77 cm3 solid, grid 0.200 mm (80x80x38), 12958 surface samples, thickness resolved to 0.100 mm

| check | status | detail |
|---|---|---|
| wall >= 1.20 mm (+/-0.10) | PASS | 0.2% of surface below (24 of 12958 samples); thinnest 0.20 mm at (-1.3, 3.9, 5.5) in 2 region(s); no region is a wall, 2 taper(s) at feature edges (0.16% of surface, budget 2%) |
| thickness distribution | PASS | median 5.80 mm, p95 14.90 mm, max 15.10 mm |
| hollowable at 1.20 mm wall | WARN | 0.27 of 0.77 cm3 (36%) in 1 pocket(s) |
| filament that would save | PASS | 0.04 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.20 mm | (-3.6, 2.7, 5.3) | 15 | 0.5 | 1.7 | 0.29 |
| 2 | taper | 0.20 mm | (-1.3, 3.9, 5.5) | 9 | 0.3 | 0.7 | 0.43 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
