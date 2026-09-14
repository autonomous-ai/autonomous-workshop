# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/heritage/part_seat_half_right.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/heritage/measure/component-rounds/seat_half_right/r0001/thickness-seat_half_right.md`

part_seat_half_right.step.py: 2.91 cm3 solid, grid 0.133 mm (410x106x117), 111120 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (52 of 111120 samples); thinnest 0.27 mm at (-18.2, 58.1, 3.6) in 2 region(s); no region is a wall, 2 taper(s) at feature edges (0.05% of surface, budget 2%); 11 more within measurement error of the limit |
| thickness distribution | PASS | median 3.53 mm, p95 14.93 mm, max 27.47 mm |
| hollowable at 1.20 mm wall | WARN | 0.75 of 2.91 cm3 (26%) in 2 pocket(s), 2 too small to shell |
| filament that would save | PASS | 0.11 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.27 mm | (-18.2, 58.1, 3.6) | 49 | 0.9 | 7.8 | 0.12 |
| 2 | taper | 0.67 mm | (-14.2, 58.3, 8.3) | 3 | 0.1 | 0.7 | 0.08 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
