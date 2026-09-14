# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_apron_left.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0005/thickness-apron_left.md`

part_apron_left.step.py: 66.63 cm3 solid, grid 0.291 mm (504x225x103), 313857 surface samples, thickness resolved to 0.146 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.15) | PASS | 0.0% of surface below (1 of 313857 samples); thinnest 0.58 mm at (138.8, -6.7, 25.4) in 1 region(s); no region is a wall, 1 taper(s) at feature edges (0.00% of surface, budget 2%) |
| thickness distribution | PASS | median 5.53 mm, p95 28.52 mm, max 146.54 mm |
| hollowable at 1.20 mm wall | WARN | 35.51 of 66.63 cm3 (53%) in 1 pocket(s) |
| filament that would save | PASS | 5.33 cm3, 6.6 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.58 mm | (138.8, -6.7, 25.4) | 1 | 0.1 | 0.0 | 0.29 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
