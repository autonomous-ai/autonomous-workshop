# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_canopy_post_middle.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0005/thickness-canopy_post_middle.md`

part_canopy_post_middle.step.py: 14.49 cm3 solid, grid 0.133 mm (117x140x710), 381778 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (1 of 381778 samples); thinnest 0.27 mm at (10.0, 1.2, 8.0) in 1 region(s); no region is a wall, 1 taper(s) at feature edges (0.00% of surface, budget 2%) |
| thickness distribution | PASS | median 3.93 mm, p95 18.00 mm, max 87.67 mm |
| hollowable at 1.20 mm wall | WARN | 3.99 of 14.49 cm3 (28%) in 1 pocket(s) |
| filament that would save | PASS | 0.60 cm3, 0.7 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.27 mm | (10.0, 1.2, 8.0) | 1 | 0.0 | 0.0 | 0.23 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
