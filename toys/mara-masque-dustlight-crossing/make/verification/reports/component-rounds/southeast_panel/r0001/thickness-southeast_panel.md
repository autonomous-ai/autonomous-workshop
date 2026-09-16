# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_southeast_panel.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/southeast_panel/r0001/thickness-southeast_panel.md`

part_southeast_panel.step.py: 78.00 cm3 solid, grid 0.207 mm (614x614x29), 370019 surface samples, thickness resolved to 0.103 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.10) | FAIL | 1.6% of surface below (2778 of 370019 samples); thinnest 0.21 mm at (9.5, 6.7, 4.7) in 20 region(s); 18 wall(s) (widest band 6.29 mm), 0 taper(s) at feature edges and 2 spot(s) too small to be a wall (0.00% of surface, budget 2%); 212 more within measurement error of the limit |
| thickness distribution | PASS | median 4.96 mm, p95 125.86 mm, max 125.97 mm |
| hollowable at 1.20 mm wall | WARN | 36.27 of 78.00 cm3 (47%) in 1 pocket(s) |
| filament that would save | PASS | 5.44 cm3, 6.7 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.21 mm | (9.5, 6.7, 4.7) | 1301 | 273.4 | 43.5 | 6.29 |
| 2 | wall | 0.41 mm | (86.1, 96.4, 4.9) | 247 | 54.5 | 22.3 | 2.44 |
| 3 | wall | 0.41 mm | (53.2, 96.4, 4.6) | 252 | 53.2 | 22.7 | 2.34 |
| 4 | wall | 0.41 mm | (60.4, 110.9, 4.7) | 239 | 51.1 | 21.8 | 2.34 |
| 5 | wall | 0.52 mm | (52.7, 124.5, 4.7) | 124 | 27.6 | 22.6 | 1.22 |
| 6 | wall | 0.52 mm | (79.9, 124.5, 4.7) | 130 | 27.6 | 22.5 | 1.23 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
