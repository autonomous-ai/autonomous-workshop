# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/part_gear_22.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/measure/rounds/r0001/thickness-gear_22.md`

part_gear_22.step.py: 2.88 cm3 solid, grid 0.133 mm (271x270x42), 157186 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (16 of 157186 samples); thinnest 0.13 mm at (-14.9, -8.9, 5.0) in 16 region(s); no region is a wall, 16 taper(s) at feature edges (0.01% of surface, budget 2%); 2 more within measurement error of the limit |
| thickness distribution | PASS | median 4.60 mm, p95 7.40 mm, max 15.47 mm |
| hollowable at 1.20 mm wall | WARN | 0.34 of 2.88 cm3 (12%) in 1 pocket(s), 90 too small to shell |
| filament that would save | PASS | 0.05 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (-14.9, -8.9, 5.0) | 1 | 0.0 | 0.0 | 0.26 |
| 2 | taper | 0.53 mm | (-3.4, 15.5, 0.0) | 1 | 0.0 | 0.0 | 0.13 |
| 3 | taper | 0.40 mm | (14.0, 9.9, 5.0) | 1 | 0.0 | 0.0 | 0.09 |
| 4 | taper | 0.73 mm | (-16.9, -4.3, 5.0) | 1 | 0.0 | 0.0 | 0.09 |
| 5 | taper | 0.60 mm | (-10.6, -13.4, 5.0) | 1 | 0.0 | 0.0 | 0.09 |
| 6 | taper | 0.20 mm | (-15.6, -5.6, 0.0) | 1 | 0.0 | 0.0 | 0.09 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
