# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/part_gear_16.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/measure/component-rounds/gear_16/r0001/thickness-gear_16.md`

part_gear_16.step.py: 1.76 cm3 solid, grid 0.133 mm (207x207x42), 100720 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (48 of 100720 samples); thinnest 0.13 mm at (-11.0, 3.3, 5.0) in 28 region(s); no region is a wall, 28 taper(s) at feature edges (0.04% of surface, budget 2%); 77 more within measurement error of the limit |
| thickness distribution | PASS | median 3.67 mm, p95 6.80 mm, max 11.20 mm |
| hollowable at 1.20 mm wall | WARN | 0.18 of 1.76 cm3 (10%) in 1 pocket(s), 30 too small to shell |
| filament that would save | PASS | 0.03 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.67 mm | (5.4, 11.8, 0.0) | 6 | 0.1 | 0.9 | 0.11 |
| 2 | taper | 0.67 mm | (5.0, 12.5, 4.8) | 5 | 0.1 | 0.7 | 0.11 |
| 3 | taper | 0.67 mm | (5.0, -12.5, 0.4) | 4 | 0.1 | 0.5 | 0.13 |
| 4 | taper | 0.67 mm | (9.4, -9.6, 4.9) | 3 | 0.0 | 0.1 | 0.35 |
| 5 | taper | 0.20 mm | (5.5, 10.3, 5.0) | 3 | 0.0 | 1.1 | 0.04 |
| 6 | taper | 0.67 mm | (9.4, -9.6, 0.4) | 2 | 0.0 | 0.0 | 0.24 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
