# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_bear_mask.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/bear_mask/r0002/thickness-bear_mask.md`

part_bear_mask.step.py: 1.11 cm3 solid, grid 0.133 mm (267x95x27), 57694 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | FAIL | 2.2% of surface below (1155 of 57694 samples); thinnest 0.60 mm at (-2.7, 6.0, 0.2) in 2 region(s); 2 wall(s) (widest band 3.60 mm) |
| thickness distribution | PASS | median 2.93 mm, p95 14.53 mm, max 34.93 mm |
| hollowable at 1.20 mm wall | WARN | 0.14 of 1.11 cm3 (12%) in 1 pocket(s) |
| filament that would save | PASS | 0.02 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.60 mm | (6.0, 6.0, 2.6) | 584 | 12.2 | 3.4 | 3.60 |
| 2 | wall | 0.60 mm | (-2.7, 6.0, 0.2) | 571 | 11.9 | 3.4 | 3.46 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
