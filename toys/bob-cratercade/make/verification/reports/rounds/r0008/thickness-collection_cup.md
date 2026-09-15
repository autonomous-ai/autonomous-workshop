# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_collection_cup.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0008/thickness-collection_cup.md`

part_collection_cup.step.py: 31.61 cm3 solid, grid 0.264 mm (255x357x122), 313259 surface samples, thickness resolved to 0.132 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.13) | FAIL | 0.4% of surface below (1164 of 313259 samples); thinnest 0.26 mm at (54.8, 3.4, 26.3) in 7 region(s); 2 wall(s) (widest band 1.74 mm), 5 taper(s) at feature edges (0.06% of surface, budget 2%); 201 more within measurement error of the limit |
| thickness distribution | PASS | median 2.90 mm, p95 30.89 mm, max 91.34 mm |
| hollowable at 1.20 mm wall | WARN | 3.72 of 31.61 cm3 (12%) in 5 pocket(s) |
| filament that would save | PASS | 0.56 cm3, 0.7 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.26 mm | (54.8, 3.4, 26.3) | 553 | 47.5 | 27.4 | 1.74 |
| 2 | wall | 0.26 mm | (11.1, 18.9, 17.6) | 440 | 38.5 | 27.4 | 1.41 |
| 3 | taper | 0.53 mm | (13.9, 51.7, 30.3) | 110 | 8.1 | 27.1 | 0.30 |
| 4 | taper | 0.40 mm | (11.0, 23.4, 30.6) | 36 | 2.8 | 13.8 | 0.20 |
| 5 | taper | 0.26 mm | (11.1, 23.7, 3.4) | 13 | 1.0 | 3.2 | 0.32 |
| 6 | taper | 0.40 mm | (11.0, 23.4, 11.1) | 8 | 0.6 | 4.8 | 0.13 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
