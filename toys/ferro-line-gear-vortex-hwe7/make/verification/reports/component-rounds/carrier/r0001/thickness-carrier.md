# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/part_carrier.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/measure/component-rounds/carrier/r0001/thickness-carrier.md`

part_carrier.step.py: 11.70 cm3 solid, grid 0.354 mm (424x344x71), 79736 surface samples, thickness resolved to 0.177 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.18) | PASS | 0.1% of surface below (87 of 79736 samples); thinnest 0.35 mm at (40.8, -0.5, 13.0) in 23 region(s); no region is a wall, 22 taper(s) at feature edges and 1 spot(s) too small to be a wall (0.06% of surface, budget 2%); 33 more within measurement error of the limit |
| thickness distribution | PASS | median 3.18 mm, p95 8.49 mm, max 51.30 mm |
| hollowable at 1.20 mm wall | WARN | 2.09 of 11.70 cm3 (18%) in 1 pocket(s) |
| filament that would save | PASS | 0.31 cm3, 0.4 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.53 mm | (72.2, -20.4, 13.5) | 9 | 0.8 | 2.1 | 0.35 |
| 2 | taper | 0.35 mm | (-37.0, -0.3, 13.2) | 9 | 0.6 | 1.4 | 0.44 |
| 3 | taper | 0.53 mm | (-68.8, 19.1, 13.5) | 8 | 0.6 | 1.7 | 0.34 |
| 4 | taper | 0.35 mm | (40.8, -0.5, 13.0) | 7 | 0.5 | 2.1 | 0.24 |
| 5 | taper | 0.35 mm | (1.8, 31.5, 23.5) | 7 | 0.5 | 2.1 | 0.23 |
| 6 | spot | 0.53 mm | (-17.0, -48.3, 13.5) | 4 | 0.4 | 0.4 | 1.05 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
