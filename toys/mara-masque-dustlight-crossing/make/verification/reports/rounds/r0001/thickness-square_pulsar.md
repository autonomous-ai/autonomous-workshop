# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_square_pulsar.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/thickness-square_pulsar.md`

part_square_pulsar.step.py: 3.08 cm3 solid, grid 0.133 mm (170x170x230), 100219 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.2% of surface below (89 of 100219 samples); thinnest 0.73 mm at (0.6, -4.6, 3.5) in 2 region(s); no region is a wall, 2 taper(s) at feature edges (0.17% of surface, budget 2%); 83 more within measurement error of the limit |
| thickness distribution | PASS | median 5.60 mm, p95 22.00 mm, max 30.00 mm |
| hollowable at 1.20 mm wall | WARN | 1.11 of 3.08 cm3 (36%) in 1 pocket(s) |
| filament that would save | PASS | 0.17 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.73 mm | (0.6, -4.6, 3.5) | 47 | 1.6 | 2.9 | 0.56 |
| 2 | taper | 0.73 mm | (-0.6, 5.4, 3.4) | 42 | 1.6 | 2.8 | 0.56 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
