# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_ribbon.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/thickness-ribbon.md`

part_ribbon.step.py: 0.35 cm3 solid, grid 0.133 mm (77x425x14), 38763 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.1% of surface below (26 of 38763 samples); thinnest 0.20 mm at (0.9, -53.9, 0.3) in 1 region(s); no region is a wall, 1 taper(s) at feature edges (0.10% of surface, budget 2%); 1 more within measurement error of the limit |
| thickness distribution | PASS | median 1.20 mm, p95 5.20 mm, max 56.00 mm |
| hollowable at 1.20 mm wall | PASS | 0.00 of 0.35 cm3 (0%) in 0 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.20 mm | (0.9, -53.9, 0.3) | 26 | 0.7 | 1.0 | 0.71 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
