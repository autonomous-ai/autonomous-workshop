# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/veinwake/part_bubble_4.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/veinwake/measure/rounds/r0001/thickness-bubble_4.md`

part_bubble_4.step.py: 6.79 cm3 solid, grid 0.133 mm (215x215x200), 161377 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (37 of 161377 samples); thinnest 0.13 mm at (1.3, 7.6, 19.7) in 10 region(s); no region is a wall, 10 taper(s) at feature edges (0.02% of surface, budget 2%); 3 more within measurement error of the limit |
| thickness distribution | PASS | median 14.60 mm, p95 27.93 mm, max 28.07 mm |
| hollowable at 1.20 mm wall | WARN | 3.52 of 6.79 cm3 (52%) in 1 pocket(s) |
| filament that would save | PASS | 0.53 cm3, 0.7 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (10.7, 5.1, 10.7) | 12 | 0.3 | 2.6 | 0.10 |
| 2 | taper | 0.13 mm | (-7.1, 11.2, 13.3) | 6 | 0.1 | 0.9 | 0.13 |
| 3 | taper | 0.13 mm | (1.3, 7.6, 19.7) | 6 | 0.1 | 0.9 | 0.13 |
| 4 | taper | 0.33 mm | (7.8, 4.7, 17.3) | 3 | 0.1 | 0.5 | 0.11 |
| 5 | taper | 0.27 mm | (-13.0, -2.4, 12.2) | 2 | 0.0 | 0.2 | 0.17 |
| 6 | taper | 0.40 mm | (2.2, 7.0, 18.9) | 2 | 0.0 | 0.4 | 0.10 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
