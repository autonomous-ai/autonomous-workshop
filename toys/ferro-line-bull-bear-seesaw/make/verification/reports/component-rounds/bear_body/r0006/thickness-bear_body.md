# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_bear_body.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/bear_body/r0006/thickness-bear_body.md`

part_bear_body.step.py: 30.72 cm3 solid, grid 0.251 mm (307x311x121), 242388 surface samples, thickness resolved to 0.126 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.13) | PASS | 0.1% of surface below (150 of 242388 samples); thinnest 0.25 mm at (1.4, 26.2, 24.8) in 13 region(s); no region is a wall, 13 taper(s) at feature edges (0.06% of surface, budget 2%); 97 more within measurement error of the limit |
| thickness distribution | PASS | median 4.27 mm, p95 42.36 mm, max 83.35 mm |
| hollowable at 1.20 mm wall | WARN | 12.50 of 30.72 cm3 (41%) in 1 pocket(s), 4 too small to shell |
| filament that would save | PASS | 1.88 cm3, 2.3 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.25 mm | (-25.5, -28.2, 18.5) | 25 | 1.7 | 2.6 | 0.68 |
| 2 | taper | 0.25 mm | (-25.4, -20.8, 20.3) | 20 | 1.4 | 2.4 | 0.57 |
| 3 | taper | 0.25 mm | (28.6, -28.2, 18.7) | 16 | 1.1 | 2.3 | 0.48 |
| 4 | taper | 0.25 mm | (1.4, 26.2, 24.8) | 15 | 1.1 | 2.3 | 0.47 |
| 5 | taper | 0.38 mm | (-28.5, -28.2, 19.2) | 13 | 0.9 | 1.9 | 0.48 |
| 6 | taper | 0.25 mm | (-28.5, -20.8, 18.2) | 12 | 0.8 | 2.6 | 0.32 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
