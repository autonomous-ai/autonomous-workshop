# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/crema_click/part_foot_plug.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/crema_click/measure/rounds/r0001/thickness-foot_plug.md`

part_foot_plug.step.py: 13.85 cm3 solid, grid 0.140 mm (404x405x73), 317616 surface samples, thickness resolved to 0.070 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (3 of 317616 samples); thinnest 0.14 mm at (-23.1, 7.6, 8.0) in 3 region(s); no region is a wall, 3 taper(s) at feature edges (0.00% of surface, budget 2%) |
| thickness distribution | PASS | median 5.46 mm, p95 55.93 mm, max 56.00 mm |
| hollowable at 1.20 mm wall | WARN | 6.62 of 13.85 cm3 (48%) in 1 pocket(s) |
| filament that would save | PASS | 0.99 cm3, 1.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.14 mm | (-23.1, 7.6, 8.0) | 1 | 0.0 | 0.0 | 0.16 |
| 2 | taper | 0.14 mm | (-18.1, 16.3, 8.0) | 1 | 0.0 | 0.0 | 0.16 |
| 3 | taper | 0.21 mm | (18.2, 16.3, 8.0) | 1 | 0.0 | 0.0 | 0.16 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
