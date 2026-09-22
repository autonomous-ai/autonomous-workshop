# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/part_rim_trim.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/measure/component-rounds/rim_trim/r0002/thickness-rim_trim.md`

part_rim_trim.step.py: 0.41 cm3 solid, grid 0.133 mm (747x747x14), 62544 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.2% of surface below (119 of 62544 samples); thinnest 0.20 mm at (-43.5, -21.2, 1.2) in 64 region(s); no region is a wall, 64 taper(s) at feature edges (0.19% of surface, budget 2%); 5 more within measurement error of the limit |
| thickness distribution | PASS | median 1.13 mm, p95 1.20 mm, max 1.27 mm |
| hollowable at 1.20 mm wall | PASS | 0.00 of 0.41 cm3 (0%) in 0 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.33 mm | (37.9, 31.8, 1.2) | 6 | 0.1 | 1.3 | 0.11 |
| 2 | taper | 0.67 mm | (-42.3, -25.7, 1.2) | 5 | 0.1 | 0.3 | 0.42 |
| 3 | taper | 0.47 mm | (45.6, -19.1, 1.2) | 4 | 0.1 | 0.3 | 0.30 |
| 4 | taper | 0.33 mm | (-32.7, 37.1, 1.2) | 4 | 0.1 | 0.4 | 0.26 |
| 5 | taper | 0.33 mm | (46.2, 14.3, 1.2) | 4 | 0.1 | 1.5 | 0.06 |
| 6 | taper | 0.60 mm | (3.8, 49.3, 1.2) | 4 | 0.1 | 0.1 | 0.65 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
