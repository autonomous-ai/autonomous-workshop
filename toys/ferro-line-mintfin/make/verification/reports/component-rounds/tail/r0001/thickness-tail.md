# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_tail.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/tail/r0001/thickness-tail.md`

part_tail.step.py: 1.55 cm3 solid, grid 0.133 mm (188x113x95), 54205 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (11 of 54205 samples); thinnest 0.13 mm at (-4.4, -5.6, 7.7) in 3 region(s); no region is a wall, 3 taper(s) at feature edges (0.02% of surface, budget 2%); 8 more within measurement error of the limit |
| thickness distribution | PASS | median 7.20 mm, p95 13.20 mm, max 16.20 mm |
| hollowable at 1.20 mm wall | WARN | 0.53 of 1.55 cm3 (34%) in 1 pocket(s) |
| filament that would save | PASS | 0.08 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.20 mm | (-4.4, 5.7, 7.6) | 6 | 0.1 | 0.4 | 0.29 |
| 2 | taper | 0.13 mm | (-2.8, -3.6, 2.5) | 3 | 0.1 | 0.1 | 0.41 |
| 3 | taper | 0.13 mm | (-4.4, -5.6, 7.7) | 2 | 0.0 | 0.3 | 0.13 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
