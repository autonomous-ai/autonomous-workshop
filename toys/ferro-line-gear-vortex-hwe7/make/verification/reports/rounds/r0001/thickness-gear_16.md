# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/part_gear_16.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/measure/rounds/r0001/thickness-gear_16.md`

part_gear_16.step.py: 1.73 cm3 solid, grid 0.133 mm (204x204x42), 99085 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (18 of 99085 samples); thinnest 0.13 mm at (-4.2, -12.0, 0.0) in 16 region(s); no region is a wall, 16 taper(s) at feature edges (0.01% of surface, budget 2%); 3 more within measurement error of the limit |
| thickness distribution | PASS | median 3.80 mm, p95 6.93 mm, max 10.93 mm |
| hollowable at 1.20 mm wall | WARN | 0.17 of 1.73 cm3 (10%) in 1 pocket(s), 28 too small to shell |
| filament that would save | PASS | 0.03 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.33 mm | (-0.9, -12.2, 4.9) | 2 | 0.0 | 0.4 | 0.07 |
| 2 | taper | 0.33 mm | (3.5, -11.2, 5.0) | 2 | 0.0 | 0.1 | 0.15 |
| 3 | taper | 0.67 mm | (-10.9, 5.5, 0.0) | 1 | 0.0 | 0.0 | 0.12 |
| 4 | taper | 0.67 mm | (11.7, -1.0, 4.9) | 1 | 0.0 | 0.0 | 0.12 |
| 5 | taper | 0.53 mm | (1.0, 11.8, 0.0) | 1 | 0.0 | 0.0 | 0.12 |
| 6 | taper | 0.53 mm | (-10.5, -5.5, 4.9) | 1 | 0.0 | 0.0 | 0.11 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
