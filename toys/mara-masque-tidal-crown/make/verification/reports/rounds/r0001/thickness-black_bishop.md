# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_black_bishop.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/thickness-black_bishop.md`

part_black_bishop.step.py: 1.27 cm3 solid, grid 0.133 mm (92x92x177), 50796 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.3% of surface below (149 of 50796 samples); thinnest 0.20 mm at (-0.1, -2.0, 22.9) in 1 region(s); no region is a wall, 1 taper(s) at feature edges (0.31% of surface, budget 2%) |
| thickness distribution | PASS | median 5.27 mm, p95 13.87 mm, max 22.93 mm |
| hollowable at 1.20 mm wall | WARN | 0.38 of 1.27 cm3 (30%) in 1 pocket(s) |
| filament that would save | PASS | 0.06 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.20 mm | (-0.1, -2.0, 22.9) | 149 | 3.0 | 4.7 | 0.63 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
