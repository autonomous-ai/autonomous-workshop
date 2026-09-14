# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_landing_ramp.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0009/thickness-landing_ramp.md`

part_landing_ramp.step.py: 52.76 cm3 solid, grid 0.306 mm (201x342x172), 163354 surface samples, thickness resolved to 0.153 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.15) | PASS | 0.1% of surface below (110 of 163354 samples); thinnest 0.31 mm at (3.6, 102.9, 41.1) in 6 region(s); no region is a wall, 6 taper(s) at feature edges (0.07% of surface, budget 2%); 22 more within measurement error of the limit |
| thickness distribution | PASS | median 9.47 mm, p95 32.09 mm, max 76.40 mm |
| hollowable at 1.20 mm wall | WARN | 33.81 of 52.76 cm3 (64%) in 1 pocket(s) |
| filament that would save | PASS | 5.07 cm3, 6.3 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.31 mm | (3.6, 102.9, 41.1) | 71 | 7.8 | 16.1 | 0.49 |
| 2 | taper | 0.46 mm | (-7.6, 102.9, 41.1) | 29 | 3.2 | 8.8 | 0.37 |
| 3 | taper | 0.46 mm | (14.7, 102.9, 51.1) | 5 | 0.6 | 1.5 | 0.42 |
| 4 | taper | 0.46 mm | (-15.7, 102.9, 51.1) | 3 | 0.4 | 1.6 | 0.25 |
| 5 | taper | 0.61 mm | (-29.9, 65.3, 1.4) | 1 | 0.1 | 0.0 | 0.30 |
| 6 | taper | 0.61 mm | (29.9, 65.3, 1.5) | 1 | 0.1 | 0.0 | 0.30 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
