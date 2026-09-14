# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_single_08.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0002/thickness-single_08.md`

part_single_08.step.py: 0.20 cm3 solid, grid 0.133 mm (95x65x35), 12205 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (2 of 12205 samples); thinnest 0.67 mm at (6.0, -0.7, 0.1) in 2 region(s); no region is a wall, 2 taper(s) at feature edges (0.01% of surface, budget 2%) |
| thickness distribution | PASS | median 4.00 mm, p95 7.87 mm, max 12.87 mm |
| hollowable at 1.20 mm wall | WARN | 0.03 of 0.20 cm3 (14%) in 1 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.67 mm | (6.0, -0.7, 0.1) | 1 | 0.0 | 0.0 | 0.13 |
| 2 | taper | 0.73 mm | (-5.8, 3.6, 0.0) | 1 | 0.0 | 0.0 | 0.10 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
