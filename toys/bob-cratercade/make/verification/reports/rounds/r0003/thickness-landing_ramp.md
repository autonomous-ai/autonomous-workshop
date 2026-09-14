# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_landing_ramp.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0003/thickness-landing_ramp.md`

part_landing_ramp.step.py: 47.62 cm3 solid, grid 0.306 mm (201x342x159), 156450 surface samples, thickness resolved to 0.153 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.15) | PASS | 0.0% of surface below (30 of 156450 samples); thinnest 0.46 mm at (2.7, 102.9, 37.1) in 10 region(s); no region is a wall, 10 taper(s) at feature edges (0.02% of surface, budget 2%); 20 more within measurement error of the limit |
| thickness distribution | PASS | median 8.25 mm, p95 32.09 mm, max 75.79 mm |
| hollowable at 1.20 mm wall | WARN | 29.98 of 47.62 cm3 (63%) in 1 pocket(s) |
| filament that would save | PASS | 4.50 cm3, 5.6 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.46 mm | (2.7, 102.9, 37.1) | 7 | 0.7 | 1.3 | 0.52 |
| 2 | taper | 0.46 mm | (14.5, 102.9, 47.1) | 4 | 0.5 | 1.2 | 0.42 |
| 3 | taper | 0.46 mm | (-12.1, 102.9, 37.1) | 5 | 0.5 | 3.1 | 0.15 |
| 4 | taper | 0.46 mm | (13.4, 102.9, 37.1) | 4 | 0.4 | 1.1 | 0.34 |
| 5 | taper | 0.61 mm | (-15.9, 103.2, 46.9) | 2 | 0.3 | 1.4 | 0.19 |
| 6 | taper | 0.46 mm | (-6.4, 102.9, 37.1) | 2 | 0.2 | 1.5 | 0.13 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
