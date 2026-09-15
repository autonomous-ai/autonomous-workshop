# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_return_hood_3.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0006/thickness-return_hood_3.md`

part_return_hood_3.step.py: 35.70 cm3 solid, grid 0.321 mm (486x303x80), 253041 surface samples, thickness resolved to 0.160 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.16) | PASS | 0.0% of surface below (2 of 253041 samples); thinnest 0.48 mm at (154.3, 72.0, 22.8) in 1 region(s); no region is a wall, 1 taper(s) at feature edges (0.00% of surface, budget 2%); 6 more within measurement error of the limit |
| thickness distribution | PASS | median 2.89 mm, p95 24.07 mm, max 170.23 mm |
| hollowable at 1.20 mm wall | WARN | 6.26 of 35.70 cm3 (18%) in 1 pocket(s), 3 too small to shell |
| filament that would save | PASS | 0.94 cm3, 1.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.48 mm | (154.3, 72.0, 22.8) | 2 | 0.3 | 0.4 | 0.61 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
