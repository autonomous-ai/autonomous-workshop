# Thickness and hollow

`artifacts/make/r0001/product/mintfin/part_face_plate.step.py --nozzle .4 --min-wall 1.2 --report artifacts/make/r0001/product/mintfin/measure/wish-thickness-face_plate.md`

part_face_plate.step.py: 4.77 cm3 solid, grid 0.200 mm (305x196x18), 105186 surface samples, thickness resolved to 0.100 mm

| check | status | detail |
|---|---|---|
| wall >= 1.20 mm (+/-0.10) | PASS | 0.0% of surface below (3 of 105186 samples); thinnest 0.20 mm at (-25.6, 13.0, -0.0) in 3 region(s); no region is a wall, 3 taper(s) at feature edges (0.00% of surface, budget 2%) |
| thickness distribution | PASS | median 2.60 mm, p95 33.50 mm, max 60.00 mm |
| hollowable at 1.20 mm wall | WARN | 0.29 of 4.77 cm3 (6%) in 1 pocket(s) |
| filament that would save | PASS | 0.04 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.20 mm | (-25.6, 13.0, -0.0) | 1 | 0.1 | 0.0 | 0.50 |
| 2 | taper | 0.60 mm | (28.3, 9.0, -0.0) | 1 | 0.0 | 0.0 | 0.23 |
| 3 | taper | 0.70 mm | (-23.6, -17.3, 0.1) | 1 | 0.0 | 0.0 | 0.20 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
