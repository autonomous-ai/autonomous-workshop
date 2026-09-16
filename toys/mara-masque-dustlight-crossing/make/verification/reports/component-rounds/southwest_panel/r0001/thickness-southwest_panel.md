# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_southwest_panel.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/southwest_panel/r0001/thickness-southwest_panel.md`

part_southwest_panel.step.py: 58.35 cm3 solid, grid 0.188 mm (516x676x31), 373803 surface samples, thickness resolved to 0.094 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.09) | FAIL | 1.0% of surface below (1787 of 373803 samples); thinnest 0.19 mm at (80.9, 68.2, 4.7) in 16 region(s); 11 wall(s) (widest band 2.36 mm), 1 taper(s) at feature edges and 4 spot(s) too small to be a wall (0.03% of surface, budget 2%); 748 more within measurement error of the limit |
| thickness distribution | PASS | median 4.88 mm, p95 95.87 mm, max 125.89 mm |
| hollowable at 1.20 mm wall | WARN | 29.18 of 58.35 cm3 (50%) in 1 pocket(s) |
| filament that would save | PASS | 4.38 cm3, 5.4 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.38 mm | (81.0, 96.9, 4.7) | 350 | 53.2 | 22.6 | 2.36 |
| 2 | wall | 0.38 mm | (52.5, 96.4, 4.6) | 346 | 51.8 | 22.9 | 2.26 |
| 3 | wall | 0.38 mm | (66.9, 109.3, 4.7) | 329 | 50.2 | 21.9 | 2.29 |
| 4 | wall | 0.47 mm | (86.5, 123.9, 4.8) | 174 | 27.1 | 22.4 | 1.21 |
| 5 | wall | 0.47 mm | (55.8, 123.9, 4.8) | 178 | 27.0 | 22.5 | 1.20 |
| 6 | wall | 0.38 mm | (36.4, 104.6, 4.6) | 160 | 25.0 | 21.8 | 1.15 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
