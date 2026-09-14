# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_collection_cup.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0004/thickness-collection_cup.md`

part_collection_cup.step.py: 34.16 cm3 solid, grid 0.264 mm (255x357x122), 329229 surface samples, thickness resolved to 0.132 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.13) | PASS | 0.1% of surface below (167 of 329229 samples); thinnest 0.26 mm at (11.1, 23.7, 3.7) in 2 region(s); no region is a wall, 2 taper(s) at feature edges (0.05% of surface, budget 2%); 51 more within measurement error of the limit |
| thickness distribution | PASS | median 2.90 mm, p95 30.89 mm, max 91.34 mm |
| hollowable at 1.20 mm wall | WARN | 4.16 of 34.16 cm3 (12%) in 5 pocket(s) |
| filament that would save | PASS | 0.62 cm3, 0.8 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.40 mm | (13.9, 51.6, 30.3) | 105 | 7.7 | 27.3 | 0.28 |
| 2 | taper | 0.26 mm | (11.1, 23.7, 3.7) | 62 | 4.7 | 26.5 | 0.18 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
