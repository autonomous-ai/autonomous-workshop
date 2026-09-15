# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_black_knight.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/thickness-black_knight.md`

part_black_knight.step.py: 1.01 cm3 solid, grid 0.133 mm (92x92x162), 41423 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.1% of surface below (34 of 41423 samples); thinnest 0.13 mm at (-4.0, 1.8, 5.0) in 2 region(s); no region is a wall, 2 taper(s) at feature edges (0.11% of surface, budget 2%) |
| thickness distribution | PASS | median 6.00 mm, p95 13.93 mm, max 20.93 mm |
| hollowable at 1.20 mm wall | WARN | 0.28 of 1.01 cm3 (27%) in 1 pocket(s) |
| filament that would save | PASS | 0.04 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (-4.0, -1.6, 5.0) | 21 | 0.5 | 1.1 | 0.45 |
| 2 | taper | 0.13 mm | (-4.0, 1.8, 5.0) | 13 | 0.4 | 0.9 | 0.45 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
