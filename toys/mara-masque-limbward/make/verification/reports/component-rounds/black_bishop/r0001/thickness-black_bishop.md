# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_black_bishop.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/black_bishop/r0001/thickness-black_bishop.md`

part_black_bishop.step.py: 1.98 cm3 solid, grid 0.133 mm (121x125x200), 78733 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (20 of 78733 samples); thinnest 0.13 mm at (-3.2, 5.3, 21.3) in 7 region(s); no region is a wall, 7 taper(s) at feature edges (0.03% of surface, budget 2%) |
| thickness distribution | PASS | median 3.93 mm, p95 16.80 mm, max 26.00 mm |
| hollowable at 1.20 mm wall | WARN | 0.45 of 1.98 cm3 (22%) in 1 pocket(s) |
| filament that would save | PASS | 0.07 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (-3.2, 5.3, 21.3) | 6 | 0.1 | 1.4 | 0.08 |
| 2 | taper | 0.13 mm | (-3.1, 5.3, 3.2) | 1 | 0.1 | 0.0 | 0.71 |
| 3 | taper | 0.13 mm | (-3.2, -5.3, 20.6) | 5 | 0.1 | 0.8 | 0.11 |
| 4 | taper | 0.13 mm | (-3.1, 5.3, 18.6) | 3 | 0.1 | 0.2 | 0.32 |
| 5 | taper | 0.13 mm | (-3.1, 5.3, 15.9) | 2 | 0.0 | 0.1 | 0.27 |
| 6 | taper | 0.13 mm | (-3.1, 5.3, 17.1) | 2 | 0.0 | 0.4 | 0.10 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
