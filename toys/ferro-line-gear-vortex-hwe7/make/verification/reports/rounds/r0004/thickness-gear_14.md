# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/part_gear_14.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/measure/rounds/r0004/thickness-gear_14.md`

part_gear_14.step.py: 1.38 cm3 solid, grid 0.133 mm (181x178x42), 79835 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (11 of 79835 samples); thinnest 0.13 mm at (10.4, 1.0, 0.0) in 10 region(s); no region is a wall, 10 taper(s) at feature edges (0.01% of surface, budget 2%); 1 more within measurement error of the limit |
| thickness distribution | PASS | median 4.93 mm, p95 9.20 mm, max 14.93 mm |
| hollowable at 1.20 mm wall | WARN | 0.14 of 1.38 cm3 (10%) in 1 pocket(s), 1 too small to shell |
| filament that would save | PASS | 0.02 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.27 mm | (-5.6, 8.7, 4.9) | 2 | 0.0 | 0.7 | 0.04 |
| 2 | taper | 0.27 mm | (3.2, 10.6, 5.0) | 1 | 0.0 | 0.0 | 0.12 |
| 3 | taper | 0.13 mm | (10.4, 1.0, 0.0) | 1 | 0.0 | 0.0 | 0.11 |
| 4 | taper | 0.20 mm | (10.4, -1.0, 5.0) | 1 | 0.0 | 0.0 | 0.11 |
| 5 | taper | 0.33 mm | (5.6, -8.7, 0.0) | 1 | 0.0 | 0.0 | 0.11 |
| 6 | taper | 0.27 mm | (8.7, 5.4, 0.0) | 1 | 0.0 | 0.0 | 0.11 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
