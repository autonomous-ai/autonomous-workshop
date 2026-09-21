# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/veinwake/part_bubble_2.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/veinwake/measure/component-rounds/bubble_2/r0001/thickness-bubble_2.md`

part_bubble_2.step.py: 6.90 cm3 solid, grid 0.133 mm (215x215x200), 162076 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (11 of 162076 samples); thinnest 0.20 mm at (-10.1, -1.7, 18.8) in 8 region(s); no region is a wall, 8 taper(s) at feature edges (0.01% of surface, budget 2%) |
| thickness distribution | PASS | median 13.47 mm, p95 27.93 mm, max 28.60 mm |
| hollowable at 1.20 mm wall | WARN | 3.61 of 6.90 cm3 (52%) in 1 pocket(s) |
| filament that would save | PASS | 0.54 cm3, 0.7 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.27 mm | (-13.6, -0.4, 4.1) | 2 | 0.0 | 0.2 | 0.19 |
| 2 | taper | 0.20 mm | (-10.1, -1.7, 18.8) | 2 | 0.0 | 0.3 | 0.11 |
| 3 | taper | 0.60 mm | (-7.2, -11.4, 12.9) | 2 | 0.0 | 0.1 | 0.26 |
| 4 | taper | 0.40 mm | (-7.1, 11.0, 13.1) | 1 | 0.0 | 0.0 | 0.15 |
| 5 | taper | 0.60 mm | (10.7, -6.7, 11.1) | 1 | 0.0 | 0.0 | 0.14 |
| 6 | taper | 0.67 mm | (10.0, 6.7, 11.1) | 1 | 0.0 | 0.0 | 0.14 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
