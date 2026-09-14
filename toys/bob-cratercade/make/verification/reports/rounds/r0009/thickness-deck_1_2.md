# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_deck_1_2.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0009/thickness-deck_1_2.md`

part_deck_1_2.step.py: 172.88 cm3 solid, grid 0.337 mm (479x479x46), 369938 surface samples, thickness resolved to 0.168 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.17) | PASS | 0.0% of surface below (9 of 369938 samples); thinnest 0.34 mm at (4.5, 144.0, 0.3) in 2 region(s); no region is a wall, 1 taper(s) at feature edges and 1 spot(s) too small to be a wall (0.00% of surface, budget 2%); 6 more within measurement error of the limit |
| thickness distribution | PASS | median 5.90 mm, p95 53.91 mm, max 206.20 mm |
| hollowable at 1.20 mm wall | WARN | 83.52 of 172.88 cm3 (48%) in 1 pocket(s) |
| filament that would save | PASS | 12.53 cm3, 15.5 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.34 mm | (4.5, 144.0, 0.3) | 5 | 1.3 | 3.0 | 0.42 |
| 2 | spot | 0.34 mm | (7.5, 143.7, 0.7) | 4 | 1.0 | 0.6 | 1.81 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
