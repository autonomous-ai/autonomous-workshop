# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_jackpot_frame.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0002/thickness-jackpot_frame.md`

part_jackpot_frame.step.py: 28.27 cm3 solid, grid 0.291 mm (355x225x149), 170740 surface samples, thickness resolved to 0.146 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.15) | FAIL | 0.1% of surface below (76 of 170740 samples); thinnest 0.29 mm at (58.0, -4.4, 6.4) in 2 region(s); 1 wall(s) (widest band 1.38 mm), 1 taper(s) at feature edges (0.02% of surface, budget 2%); 9 more within measurement error of the limit |
| thickness distribution | PASS | median 5.82 mm, p95 33.47 mm, max 101.87 mm |
| hollowable at 1.20 mm wall | WARN | 12.64 of 28.27 cm3 (45%) in 1 pocket(s) |
| filament that would save | PASS | 1.90 cm3, 2.4 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.29 mm | (58.0, -4.4, 6.4) | 48 | 5.1 | 3.7 | 1.38 |
| 2 | taper | 0.29 mm | (58.0, -7.8, 5.3) | 28 | 2.8 | 3.6 | 0.80 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
