# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/heritage/part_handlebar.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/heritage/measure/component-rounds/handlebar/r0001/thickness-handlebar.md`

part_handlebar.step.py: 1.20 cm3 solid, grid 0.133 mm (144x586x31), 62789 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.2% of surface below (119 of 62789 samples); thinnest 0.20 mm at (23.5, -38.6, 0.3) in 2 region(s); no region is a wall, 2 taper(s) at feature edges (0.20% of surface, budget 2%); 5 more within measurement error of the limit |
| thickness distribution | PASS | median 3.47 mm, p95 7.93 mm, max 8.93 mm |
| hollowable at 1.20 mm wall | WARN | 0.16 of 1.20 cm3 (13%) in 1 pocket(s) |
| filament that would save | PASS | 0.02 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.20 mm | (23.5, -38.6, 0.3) | 62 | 1.3 | 2.7 | 0.47 |
| 2 | taper | 0.20 mm | (23.6, 38.8, 1.1) | 57 | 1.2 | 2.7 | 0.44 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
