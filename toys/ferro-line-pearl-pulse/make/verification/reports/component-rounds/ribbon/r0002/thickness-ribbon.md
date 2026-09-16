# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_ribbon.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/ribbon/r0002/thickness-ribbon.md`

part_ribbon.step.py: 0.35 cm3 solid, grid 0.133 mm (77x425x14), 38692 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.2% of surface below (56 of 38692 samples); thinnest 0.13 mm at (2.5, -53.9, 0.4) in 1 region(s); no region is a wall, 0 taper(s) at feature edges and 1 spot(s) too small to be a wall (0.18% of surface, budget 2%); 15 more within measurement error of the limit |
| thickness distribution | PASS | median 1.20 mm, p95 5.20 mm, max 56.00 mm |
| hollowable at 1.20 mm wall | PASS | 0.00 of 0.35 cm3 (0%) in 0 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | spot | 0.13 mm | (2.5, -53.9, 0.4) | 56 | 1.4 | 1.2 | 1.19 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
