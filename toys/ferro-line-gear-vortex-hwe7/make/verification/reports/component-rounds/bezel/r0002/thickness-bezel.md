# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/part_bezel.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/measure/component-rounds/bezel/r0002/thickness-bezel.md`

part_bezel.step.py: 4.65 cm3 solid, grid 0.133 mm (530x530x35), 208389 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.5% of surface below (325 of 208389 samples); thinnest 0.13 mm at (-26.2, 23.2, 3.8) in 117 region(s); no region is a wall, 105 taper(s) at feature edges and 12 spot(s) too small to be a wall (0.46% of surface, budget 2%); 23 more within measurement error of the limit |
| thickness distribution | PASS | median 4.00 mm, p95 6.00 mm, max 29.33 mm |
| hollowable at 1.20 mm wall | WARN | 0.98 of 4.65 cm3 (21%) in 2 pocket(s), 1 too small to shell |
| filament that would save | PASS | 0.15 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.33 mm | (-21.8, -27.4, 3.7) | 10 | 0.6 | 2.7 | 0.24 |
| 2 | taper | 0.40 mm | (8.7, 33.8, 3.3) | 5 | 0.5 | 0.9 | 0.55 |
| 3 | taper | 0.13 mm | (21.8, -27.4, 3.7) | 7 | 0.4 | 2.5 | 0.17 |
| 4 | taper | 0.33 mm | (-27.0, -22.3, 3.7) | 7 | 0.4 | 0.8 | 0.50 |
| 5 | taper | 0.20 mm | (-5.1, 34.6, 3.8) | 7 | 0.4 | 0.9 | 0.45 |
| 6 | taper | 0.13 mm | (-34.5, 5.8, 3.4) | 6 | 0.4 | 0.8 | 0.51 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
