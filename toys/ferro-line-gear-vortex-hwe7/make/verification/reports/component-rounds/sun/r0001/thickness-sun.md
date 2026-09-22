# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/part_sun.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/measure/component-rounds/sun/r0001/thickness-sun.md`

part_sun.step.py: 6.12 cm3 solid, grid 0.133 mm (429x429x42), 310760 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (40 of 310760 samples); thinnest 0.13 mm at (25.8, -1.3, 5.0) in 34 region(s); no region is a wall, 34 taper(s) at feature edges (0.01% of surface, budget 2%); 4 more within measurement error of the limit |
| thickness distribution | PASS | median 4.93 mm, p95 8.13 mm, max 11.87 mm |
| hollowable at 1.20 mm wall | WARN | 1.10 of 6.12 cm3 (18%) in 7 pocket(s), 181 too small to shell |
| filament that would save | PASS | 0.16 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.40 mm | (0.9, -27.3, 5.0) | 2 | 0.0 | 0.7 | 0.04 |
| 2 | taper | 0.20 mm | (-3.8, 26.9, 5.0) | 2 | 0.0 | 0.6 | 0.05 |
| 3 | taper | 0.13 mm | (-7.7, -24.8, 5.0) | 2 | 0.0 | 0.6 | 0.05 |
| 4 | taper | 0.60 mm | (-1.3, -25.8, 4.9) | 2 | 0.0 | 0.8 | 0.03 |
| 5 | taper | 0.53 mm | (-11.8, 23.0, 5.0) | 2 | 0.0 | 0.7 | 0.04 |
| 6 | taper | 0.13 mm | (25.8, -1.3, 5.0) | 2 | 0.0 | 0.4 | 0.07 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
