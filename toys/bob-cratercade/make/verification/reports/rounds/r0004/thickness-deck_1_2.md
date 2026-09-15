# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_deck_1_2.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0004/thickness-deck_1_2.md`

part_deck_1_2.step.py: 172.84 cm3 solid, grid 0.337 mm (479x479x46), 369735 surface samples, thickness resolved to 0.168 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.17) | PASS | 0.0% of surface below (10 of 369735 samples); thinnest 0.34 mm at (0.1, 135.7, 0.4) in 4 region(s); no region is a wall, 0 taper(s) at feature edges and 4 spot(s) too small to be a wall (0.00% of surface, budget 2%); 3 more within measurement error of the limit |
| thickness distribution | PASS | median 5.90 mm, p95 53.40 mm, max 206.37 mm |
| hollowable at 1.20 mm wall | WARN | 83.49 of 172.84 cm3 (48%) in 1 pocket(s) |
| filament that would save | PASS | 12.52 cm3, 15.5 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | spot | 0.51 mm | (0.3, 148.4, 0.4) | 3 | 1.1 | 0.4 | 2.53 |
| 2 | spot | 0.34 mm | (0.1, 135.7, 0.4) | 3 | 0.7 | 0.7 | 0.93 |
| 3 | spot | 0.34 mm | (4.3, 144.0, 0.8) | 2 | 0.6 | 0.5 | 1.40 |
| 4 | spot | 0.34 mm | (7.5, 144.0, 0.5) | 2 | 0.5 | 0.5 | 1.08 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
