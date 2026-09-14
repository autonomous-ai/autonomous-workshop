# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/heritage/part_seat_half.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/heritage/measure/component-rounds/seat_half/r0001/thickness-seat_half.md`

part_seat_half.step.py: 2.88 cm3 solid, grid 0.133 mm (410x106x117), 111056 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (50 of 111056 samples); thinnest 0.33 mm at (-18.6, -58.1, 2.8) in 3 region(s); no region is a wall, 3 taper(s) at feature edges (0.05% of surface, budget 2%); 11 more within measurement error of the limit |
| thickness distribution | PASS | median 3.53 mm, p95 14.93 mm, max 27.67 mm |
| hollowable at 1.20 mm wall | WARN | 0.73 of 2.88 cm3 (25%) in 2 pocket(s), 3 too small to shell |
| filament that would save | PASS | 0.11 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.33 mm | (-18.6, -58.1, 2.8) | 43 | 0.8 | 7.8 | 0.11 |
| 2 | taper | 0.47 mm | (-14.4, -58.5, 8.3) | 6 | 0.1 | 0.5 | 0.26 |
| 3 | taper | 0.73 mm | (-14.0, -58.4, 12.1) | 1 | 0.0 | 0.0 | 0.15 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
