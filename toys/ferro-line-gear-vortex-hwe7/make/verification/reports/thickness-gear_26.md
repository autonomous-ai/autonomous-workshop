# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/part_gear_26.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/measure/rounds/r0004/thickness-gear_26.md`

part_gear_26.step.py: 3.73 cm3 solid, grid 0.133 mm (316x315x42), 196921 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (24 of 196921 samples); thinnest 0.13 mm at (18.4, 5.6, 5.0) in 21 region(s); no region is a wall, 21 taper(s) at feature edges (0.01% of surface, budget 2%); 3 more within measurement error of the limit |
| thickness distribution | PASS | median 4.93 mm, p95 7.67 mm, max 18.47 mm |
| hollowable at 1.20 mm wall | WARN | 0.51 of 3.73 cm3 (14%) in 2 pocket(s), 133 too small to shell |
| filament that would save | PASS | 0.08 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.33 mm | (20.7, 0.5, 5.0) | 2 | 0.0 | 0.0 | 0.25 |
| 2 | taper | 0.53 mm | (18.0, 5.6, 0.0) | 2 | 0.0 | 0.5 | 0.05 |
| 3 | taper | 0.20 mm | (18.0, -5.6, 5.0) | 2 | 0.0 | 0.0 | 0.19 |
| 4 | taper | 0.67 mm | (-18.1, -10.1, 5.0) | 1 | 0.0 | 0.0 | 0.13 |
| 5 | taper | 0.60 mm | (17.7, -10.0, 5.0) | 1 | 0.0 | 0.0 | 0.10 |
| 6 | taper | 0.53 mm | (-19.6, 4.0, 5.0) | 1 | 0.0 | 0.0 | 0.10 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
