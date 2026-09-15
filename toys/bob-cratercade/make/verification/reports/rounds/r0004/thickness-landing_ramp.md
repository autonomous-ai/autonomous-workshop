# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_landing_ramp.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0004/thickness-landing_ramp.md`

part_landing_ramp.step.py: 53.28 cm3 solid, grid 0.306 mm (201x342x172), 162527 surface samples, thickness resolved to 0.153 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.15) | PASS | 0.1% of surface below (101 of 162527 samples); thinnest 0.31 mm at (-6.5, 102.9, 41.1) in 4 region(s); no region is a wall, 4 taper(s) at feature edges (0.07% of surface, budget 2%); 16 more within measurement error of the limit |
| thickness distribution | PASS | median 9.47 mm, p95 32.09 mm, max 76.40 mm |
| hollowable at 1.20 mm wall | WARN | 34.61 of 53.28 cm3 (65%) in 1 pocket(s) |
| filament that would save | PASS | 5.19 cm3, 6.4 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.31 mm | (-6.5, 102.9, 41.1) | 91 | 10.3 | 26.3 | 0.39 |
| 2 | taper | 0.31 mm | (14.2, 102.9, 51.1) | 6 | 0.8 | 1.4 | 0.58 |
| 3 | taper | 0.61 mm | (-15.4, 102.8, 51.1) | 3 | 0.4 | 1.2 | 0.32 |
| 4 | taper | 0.61 mm | (29.9, 65.3, 1.4) | 1 | 0.1 | 0.0 | 0.30 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
