# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_head.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/head/r0002/thickness-head.md`

part_head.step.py: 19.63 cm3 solid, grid 0.170 mm (229x322x152), 199132 surface samples, thickness resolved to 0.085 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.09) | PASS | 0.0% of surface below (66 of 199132 samples); thinnest 0.26 mm at (9.4, -14.3, 20.4) in 2 region(s); no region is a wall, 2 taper(s) at feature edges (0.04% of surface, budget 2%); 77 more within measurement error of the limit |
| thickness distribution | PASS | median 17.53 mm, p95 44.24 mm, max 55.39 mm |
| hollowable at 1.20 mm wall | WARN | 13.29 of 19.63 cm3 (68%) in 2 pocket(s) |
| filament that would save | PASS | 1.99 cm3, 2.5 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.26 mm | (11.0, 14.4, 20.4) | 38 | 1.6 | 2.8 | 0.58 |
| 2 | taper | 0.26 mm | (9.4, -14.3, 20.4) | 28 | 1.1 | 2.7 | 0.39 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
