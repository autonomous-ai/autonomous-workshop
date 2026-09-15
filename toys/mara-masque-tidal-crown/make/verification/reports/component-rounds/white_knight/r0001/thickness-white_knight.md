# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_white_knight.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/white_knight/r0001/thickness-white_knight.md`

part_white_knight.step.py: 1.09 cm3 solid, grid 0.133 mm (110x110x162), 44933 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.1% of surface below (40 of 44933 samples); thinnest 0.13 mm at (-4.0, 2.4, 5.0) in 2 region(s); no region is a wall, 2 taper(s) at feature edges (0.10% of surface, budget 2%) |
| thickness distribution | PASS | median 5.27 mm, p95 14.00 mm, max 20.93 mm |
| hollowable at 1.20 mm wall | WARN | 0.29 of 1.09 cm3 (27%) in 1 pocket(s) |
| filament that would save | PASS | 0.04 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (-4.0, 2.4, 5.0) | 20 | 0.4 | 1.0 | 0.42 |
| 2 | taper | 0.13 mm | (-4.0, -1.6, 5.0) | 20 | 0.4 | 0.9 | 0.44 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
