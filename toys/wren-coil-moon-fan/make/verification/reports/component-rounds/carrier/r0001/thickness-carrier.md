# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_carrier.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/carrier/r0001/thickness-carrier.md`

part_carrier.step.py: 6.87 cm3 solid, grid 0.133 mm (447x605x39), 296494 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | FAIL | 0.4% of surface below (1069 of 296494 samples); thinnest 0.13 mm at (-17.7, 9.2, 2.1) in 2 region(s); 2 wall(s) (widest band 3.28 mm); 172 more within measurement error of the limit |
| thickness distribution | PASS | median 4.53 mm, p95 17.67 mm, max 52.13 mm |
| hollowable at 1.20 mm wall | WARN | 1.81 of 6.87 cm3 (26%) in 3 pocket(s) |
| filament that would save | PASS | 0.27 cm3, 0.3 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.13 mm | (-17.7, -9.2, 2.8) | 538 | 10.9 | 3.3 | 3.28 |
| 2 | wall | 0.13 mm | (-17.7, 9.2, 2.1) | 531 | 10.6 | 3.3 | 3.23 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
