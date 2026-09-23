# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_face_plate.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/rounds/r0001/thickness-face_plate.md`

part_face_plate.step.py: 4.64 cm3 solid, grid 0.133 mm (455x291x24), 238409 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (3 of 238409 samples); thinnest 0.13 mm at (-25.5, 13.1, 2.5) in 3 region(s); no region is a wall, 3 taper(s) at feature edges (0.00% of surface, budget 2%) |
| thickness distribution | PASS | median 2.53 mm, p95 33.47 mm, max 60.00 mm |
| hollowable at 1.20 mm wall | WARN | 0.19 of 4.64 cm3 (4%) in 1 pocket(s) |
| filament that would save | PASS | 0.03 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.67 mm | (-23.6, -17.3, 2.5) | 1 | 0.0 | 0.0 | 0.13 |
| 2 | taper | 0.13 mm | (-25.5, 13.1, 2.5) | 1 | 0.0 | 0.0 | 0.13 |
| 3 | taper | 0.33 mm | (18.2, -19.2, 0.0) | 1 | 0.0 | 0.0 | 0.13 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
