# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_collection_cup.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0009/thickness-collection_cup.md`

part_collection_cup.step.py: 32.14 cm3 solid, grid 0.264 mm (255x376x122), 311786 surface samples, thickness resolved to 0.132 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.13) | PASS | 0.1% of surface below (168 of 311786 samples); thinnest 0.40 mm at (11.0, 28.4, 24.4) in 4 region(s); no region is a wall, 4 taper(s) at feature edges (0.06% of surface, budget 2%); 28 more within measurement error of the limit |
| thickness distribution | PASS | median 2.90 mm, p95 30.89 mm, max 96.36 mm |
| hollowable at 1.20 mm wall | WARN | 3.99 of 32.14 cm3 (12%) in 3 pocket(s) |
| filament that would save | PASS | 0.60 cm3, 0.7 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.53 mm | (13.9, 56.7, 30.7) | 106 | 7.9 | 27.2 | 0.29 |
| 2 | taper | 0.40 mm | (11.0, 28.4, 12.9) | 38 | 2.9 | 10.6 | 0.27 |
| 3 | taper | 0.40 mm | (11.0, 28.4, 24.4) | 14 | 1.1 | 7.8 | 0.14 |
| 4 | taper | 0.40 mm | (11.0, 28.3, 17.9) | 10 | 0.8 | 4.1 | 0.18 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
