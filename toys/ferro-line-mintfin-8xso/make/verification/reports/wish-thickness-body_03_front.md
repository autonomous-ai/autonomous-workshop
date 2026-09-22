# Thickness and hollow

`artifacts/make/r0001/product/mintfin/part_body_03_front.step.py --nozzle .4 --min-wall 1.2 --report artifacts/make/r0001/product/mintfin/measure/wish-thickness-body_03_front.md`

part_body_03_front.step.py: 2.40 cm3 solid, grid 0.200 mm (270x208x57), 90344 surface samples, thickness resolved to 0.100 mm

| check | status | detail |
|---|---|---|
| wall >= 1.20 mm (+/-0.10) | PASS | 0.0% of surface below (2 of 90344 samples); thinnest 0.60 mm at (-18.3, 15.2, 0.0) in 2 region(s); no region is a wall, 2 taper(s) at feature edges (0.00% of surface, budget 2%); 39229 more within measurement error of the limit |
| thickness distribution | PASS | median 1.20 mm, p95 9.60 mm, max 53.00 mm |
| hollowable at 1.20 mm wall | WARN | 0.18 of 2.40 cm3 (8%) in 1 pocket(s) |
| filament that would save | PASS | 0.03 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.60 mm | (-18.3, 15.2, 0.0) | 1 | 0.1 | 0.0 | 0.26 |
| 2 | taper | 0.80 mm | (-7.5, -20.1, 0.1) | 1 | 0.0 | 0.0 | 0.25 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
