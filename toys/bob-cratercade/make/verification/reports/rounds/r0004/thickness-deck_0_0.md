# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_deck_0_0.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0004/thickness-deck_0_0.md`

part_deck_0_0.step.py: 154.14 cm3 solid, grid 0.337 mm (479x479x46), 381139 surface samples, thickness resolved to 0.168 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.17) | PASS | 0.0% of surface below (19 of 381139 samples); thinnest 0.34 mm at (112.4, 160.0, 5.5) in 2 region(s); no region is a wall, 2 taper(s) at feature edges (0.00% of surface, budget 2%); 10 more within measurement error of the limit |
| thickness distribution | PASS | median 6.06 mm, p95 81.20 mm, max 203.50 mm |
| hollowable at 1.20 mm wall | WARN | 78.90 of 154.14 cm3 (51%) in 1 pocket(s) |
| filament that would save | PASS | 11.83 cm3, 14.7 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.34 mm | (112.4, 160.0, 5.5) | 12 | 1.9 | 5.9 | 0.32 |
| 2 | taper | 0.34 mm | (116.2, 159.7, 4.1) | 7 | 1.0 | 2.2 | 0.43 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
