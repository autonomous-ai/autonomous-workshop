# Thickness and hollow

`artifacts/make/r0001/product/heritage/part_front_fender.step.py --nozzle 0.4 --report artifacts/make/r0001/product/heritage/measure/thickness-front_fender.md`

part_front_fender.step.py: 3.37 cm3 solid, grid 0.133 mm (473x176x114), 151877 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (2 of 151877 samples); thinnest 0.60 mm at (38.9, -38.3, 14.4) in 1 region(s); no region is a wall, 1 taper(s) at feature edges (0.00% of surface, budget 2%); 1 more within measurement error of the limit |
| thickness distribution | PASS | median 3.00 mm, p95 14.53 mm, max 14.53 mm |
| hollowable at 1.20 mm wall | WARN | 0.45 of 3.37 cm3 (13%) in 1 pocket(s) |
| filament that would save | PASS | 0.07 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.60 mm | (38.9, -38.3, 14.4) | 2 | 0.0 | 0.0 | 0.30 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
