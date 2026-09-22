# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/part_carrier.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/measure/rounds/r0002/thickness-carrier.md`

part_carrier.step.py: 11.37 cm3 solid, grid 0.354 mm (424x344x71), 78509 surface samples, thickness resolved to 0.177 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.18) | PASS | 0.1% of surface below (90 of 78509 samples); thinnest 0.35 mm at (-1.2, -30.2, 23.5) in 19 region(s); no region is a wall, 19 taper(s) at feature edges (0.06% of surface, budget 2%); 41 more within measurement error of the limit |
| thickness distribution | PASS | median 3.18 mm, p95 7.08 mm, max 51.30 mm |
| hollowable at 1.20 mm wall | WARN | 1.90 of 11.37 cm3 (17%) in 1 pocket(s) |
| filament that would save | PASS | 0.28 cm3, 0.4 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.53 mm | (-40.4, 1.0, 13.5) | 8 | 0.8 | 1.3 | 0.62 |
| 2 | taper | 0.35 mm | (38.4, 25.9, 13.2) | 10 | 0.7 | 2.0 | 0.37 |
| 3 | taper | 0.53 mm | (43.5, -46.3, 13.5) | 8 | 0.7 | 1.2 | 0.57 |
| 4 | taper | 0.35 mm | (-1.2, -30.2, 23.5) | 8 | 0.6 | 2.6 | 0.23 |
| 5 | taper | 0.35 mm | (-20.3, -47.1, 13.1) | 7 | 0.4 | 2.1 | 0.20 |
| 6 | taper | 0.35 mm | (69.1, -20.7, 13.2) | 7 | 0.4 | 2.0 | 0.19 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
