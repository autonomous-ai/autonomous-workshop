# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/veinwake/part_rind.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/veinwake/measure/component-rounds/rind/r0001/thickness-rind.md`

part_rind.step.py: 129.51 cm3 solid, grid 0.291 mm (486x451x53), 381480 surface samples, thickness resolved to 0.146 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.15) | PASS | 0.1% of surface below (299 of 381480 samples); thinnest 0.29 mm at (-55.4, -57.4, 0.0) in 45 region(s); no region is a wall, 45 taper(s) at feature edges (0.08% of surface, budget 2%); 167 more within measurement error of the limit |
| thickness distribution | PASS | median 7.86 mm, p95 21.25 mm, max 62.72 mm |
| hollowable at 1.20 mm wall | WARN | 82.55 of 129.51 cm3 (64%) in 1 pocket(s) |
| filament that would save | PASS | 12.38 cm3, 15.4 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.29 mm | (-68.8, -6.0, 0.0) | 34 | 3.6 | 19.0 | 0.19 |
| 2 | taper | 0.29 mm | (68.1, 2.6, 0.0) | 30 | 3.1 | 13.7 | 0.23 |
| 3 | taper | 0.44 mm | (66.7, -15.2, 0.3) | 23 | 2.4 | 11.7 | 0.21 |
| 4 | taper | 0.29 mm | (62.7, 51.2, 0.0) | 17 | 1.9 | 6.9 | 0.28 |
| 5 | taper | 0.29 mm | (69.9, 21.5, 0.2) | 17 | 1.8 | 5.6 | 0.31 |
| 6 | taper | 0.29 mm | (-68.7, -42.3, 0.0) | 16 | 1.8 | 7.6 | 0.23 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
