# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_gills_left.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/gills_left/r0001/thickness-gills_left.md`

part_gills_left.step.py: 1.74 cm3 solid, grid 0.133 mm (286x391x32), 101689 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (4 of 101689 samples); thinnest 0.13 mm at (-4.4, -4.8, 2.5) in 3 region(s); no region is a wall, 3 taper(s) at feature edges (0.00% of surface, budget 2%); 1 more within measurement error of the limit |
| thickness distribution | PASS | median 2.40 mm, p95 11.47 mm, max 37.80 mm |
| hollowable at 1.20 mm wall | WARN | 0.02 of 1.74 cm3 (1%) in 3 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.27 mm | (-4.7, 4.1, 2.6) | 2 | 0.0 | 0.1 | 0.25 |
| 2 | taper | 0.13 mm | (-4.4, -4.8, 2.5) | 1 | 0.0 | 0.0 | 0.13 |
| 3 | taper | 0.20 mm | (-3.8, -6.5, 3.6) | 1 | 0.0 | 0.0 | 0.13 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
