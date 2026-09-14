# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/heritage/part_seat_half.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/heritage/measure/rounds/r0001/thickness-seat_half.md`

part_seat_half.step.py: 2.71 cm3 solid, grid 0.133 mm (372x106x117), 104840 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.2% of surface below (191 of 104840 samples); thinnest 0.13 mm at (-19.0, -58.0, 13.9) in 1 region(s); no region is a wall, 1 taper(s) at feature edges (0.20% of surface, budget 2%); 19 more within measurement error of the limit |
| thickness distribution | PASS | median 3.47 mm, p95 14.93 mm, max 24.87 mm |
| hollowable at 1.20 mm wall | WARN | 0.69 of 2.71 cm3 (25%) in 2 pocket(s), 3 too small to shell |
| filament that would save | PASS | 0.10 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (-19.0, -58.0, 13.9) | 191 | 3.9 | 14.5 | 0.27 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
