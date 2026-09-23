# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_bear_body.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/bear_body/r0004/thickness-bear_body.md`

part_bear_body.step.py: 31.68 cm3 solid, grid 0.251 mm (307x311x121), 240911 surface samples, thickness resolved to 0.126 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.13) | PASS | 0.1% of surface below (142 of 240911 samples); thinnest 0.25 mm at (-1.5, 26.3, 26.4) in 12 region(s); no region is a wall, 12 taper(s) at feature edges (0.06% of surface, budget 2%); 91 more within measurement error of the limit |
| thickness distribution | PASS | median 4.27 mm, p95 42.11 mm, max 83.35 mm |
| hollowable at 1.20 mm wall | WARN | 13.59 of 31.68 cm3 (43%) in 1 pocket(s) |
| filament that would save | PASS | 2.04 cm3, 2.5 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.25 mm | (-25.5, -28.2, 18.3) | 23 | 1.6 | 2.6 | 0.62 |
| 2 | taper | 0.38 mm | (28.6, -20.9, 20.1) | 18 | 1.2 | 2.4 | 0.51 |
| 3 | taper | 0.25 mm | (28.6, -28.2, 20.5) | 16 | 1.1 | 2.5 | 0.45 |
| 4 | taper | 0.25 mm | (-1.6, 34.7, 26.7) | 13 | 0.9 | 2.2 | 0.40 |
| 5 | taper | 0.25 mm | (-27.1, -28.5, 20.6) | 12 | 0.9 | 3.0 | 0.28 |
| 6 | taper | 0.25 mm | (-28.5, -20.8, 18.8) | 13 | 0.8 | 2.4 | 0.34 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
