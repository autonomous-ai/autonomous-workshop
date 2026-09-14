# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/heritage/part_pannier.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/heritage/measure/component-rounds/pannier/r0001/thickness-pannier.md`

part_pannier.step.py: 10.68 cm3 solid, grid 0.133 mm (290x185x95), 167728 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.1% of surface below (47 of 167728 samples); thinnest 0.47 mm at (-85.5, 55.0, 11.9) in 2 region(s); no region is a wall, 2 taper(s) at feature edges (0.05% of surface, budget 2%) |
| thickness distribution | PASS | median 12.00 mm, p95 38.00 mm, max 38.00 mm |
| hollowable at 1.20 mm wall | WARN | 7.20 of 10.68 cm3 (67%) in 1 pocket(s) |
| filament that would save | PASS | 1.08 cm3, 1.3 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.47 mm | (-50.5, 54.5, 11.9) | 25 | 0.8 | 1.1 | 0.72 |
| 2 | taper | 0.47 mm | (-85.5, 55.0, 11.9) | 22 | 0.8 | 1.1 | 0.76 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
