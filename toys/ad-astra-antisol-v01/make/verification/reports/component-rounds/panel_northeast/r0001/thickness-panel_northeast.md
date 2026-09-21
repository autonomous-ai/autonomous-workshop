# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_panel_northeast.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/panel_northeast/r0001/thickness-panel_northeast.md`

part_panel_northeast.step.py: 203.20 cm3 solid, grid 0.306 mm (502x620x34), 378977 surface samples, thickness resolved to 0.153 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.15) | FAIL | 2.4% of surface below (8590 of 378977 samples); thinnest 0.46 mm at (-75.4, 51.6, 7.7) in 2 region(s); 2 wall(s) (widest band 11.75 mm); 41 more within measurement error of the limit |
| thickness distribution | PASS | median 8.86 mm, p95 116.59 mm, max 187.95 mm |
| hollowable at 1.20 mm wall | WARN | 123.93 of 203.20 cm3 (61%) in 1 pocket(s) |
| filament that would save | PASS | 18.59 cm3, 23.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.46 mm | (30.4, -93.4, 4.7) | 4304 | 823.8 | 70.1 | 11.75 |
| 2 | wall | 0.46 mm | (-75.4, 51.6, 7.7) | 4286 | 822.9 | 70.7 | 11.64 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
