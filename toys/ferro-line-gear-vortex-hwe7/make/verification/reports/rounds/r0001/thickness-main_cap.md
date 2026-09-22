# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/part_main_cap.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/measure/rounds/r0001/thickness-main_cap.md`

part_main_cap.step.py: 1.32 cm3 solid, grid 0.133 mm (177x177x59), 65882 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 1.7% of surface below (1022 of 65882 samples); thinnest 0.13 mm at (-1.5, 8.4, 0.0) in 3 region(s); no region is a wall, 3 taper(s) at feature edges (1.73% of surface, budget 2%); 113 more within measurement error of the limit |
| thickness distribution | PASS | median 3.13 mm, p95 7.20 mm, max 7.20 mm |
| hollowable at 1.20 mm wall | WARN | 0.08 of 1.32 cm3 (6%) in 1 pocket(s), 12 too small to shell |
| filament that would save | PASS | 0.01 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (-1.8, -8.2, 7.1) | 522 | 11.8 | 15.8 | 0.74 |
| 2 | taper | 0.13 mm | (-1.5, 8.4, 0.0) | 498 | 11.1 | 14.2 | 0.78 |
| 3 | taper | 0.67 mm | (-8.2, 2.1, 0.0) | 2 | 0.1 | 0.7 | 0.07 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
