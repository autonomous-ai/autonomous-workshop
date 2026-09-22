# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/part_gear_cap.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/measure/component-rounds/gear_cap/r0002/thickness-gear_cap.md`

part_gear_cap.step.py: 0.13 cm3 solid, grid 0.133 mm (59x59x41), 10833 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (2 of 10833 samples); thinnest 0.13 mm at (-1.6, 0.8, 4.1) in 1 region(s); no region is a wall, 1 taper(s) at feature edges (0.02% of surface, budget 2%); 1 more within measurement error of the limit |
| thickness distribution | PASS | median 1.80 mm, p95 4.80 mm, max 4.80 mm |
| hollowable at 1.20 mm wall | PASS | 0.00 of 0.13 cm3 (0%) in 0 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (-1.6, 0.8, 4.1) | 2 | 0.0 | 0.5 | 0.07 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
