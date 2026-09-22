# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/part_gear_24.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/measure/component-rounds/gear_24/r0001/thickness-gear_24.md`

part_gear_24.step.py: 3.29 cm3 solid, grid 0.133 mm (294x294x42), 176716 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (14 of 176716 samples); thinnest 0.13 mm at (-5.5, -18.2, 5.0) in 13 region(s); no region is a wall, 13 taper(s) at feature edges (0.01% of surface, budget 2%); 3 more within measurement error of the limit |
| thickness distribution | PASS | median 4.93 mm, p95 7.47 mm, max 16.93 mm |
| hollowable at 1.20 mm wall | WARN | 0.42 of 3.29 cm3 (13%) in 2 pocket(s), 114 too small to shell |
| filament that would save | PASS | 0.06 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.60 mm | (10.0, 15.6, 0.0) | 2 | 0.0 | 0.0 | 0.19 |
| 2 | taper | 0.13 mm | (-5.5, -18.2, 5.0) | 1 | 0.0 | 0.0 | 0.10 |
| 3 | taper | 0.20 mm | (-18.4, 4.3, 0.0) | 1 | 0.0 | 0.0 | 0.10 |
| 4 | taper | 0.60 mm | (-12.9, 13.8, 0.0) | 1 | 0.0 | 0.0 | 0.10 |
| 5 | taper | 0.40 mm | (-10.0, -15.6, 5.0) | 1 | 0.0 | 0.0 | 0.09 |
| 6 | taper | 0.20 mm | (-16.4, 8.5, 5.0) | 1 | 0.0 | 0.0 | 0.09 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
