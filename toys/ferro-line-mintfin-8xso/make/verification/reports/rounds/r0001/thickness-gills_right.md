# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_gills_right.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/rounds/r0001/thickness-gills_right.md`

part_gills_right.step.py: 1.73 cm3 solid, grid 0.133 mm (286x391x32), 101594 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (1 of 101594 samples); thinnest 0.13 mm at (3.0, 9.7, 2.5) in 1 region(s); no region is a wall, 1 taper(s) at feature edges (0.00% of surface, budget 2%) |
| thickness distribution | PASS | median 2.40 mm, p95 11.47 mm, max 37.73 mm |
| hollowable at 1.20 mm wall | WARN | 0.02 of 1.73 cm3 (1%) in 3 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (3.0, 9.7, 2.5) | 1 | 0.0 | 0.0 | 0.13 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
