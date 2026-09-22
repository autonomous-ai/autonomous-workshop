# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_03_front.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/body_03_front/r0002/thickness-body_03_front.md`

part_body_03_front.step.py: 5.17 cm3 solid, grid 0.133 mm (403x310x83), 209304 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (19 of 209304 samples); thinnest 0.13 mm at (1.3, 15.9, 3.2) in 4 region(s); no region is a wall, 4 taper(s) at feature edges (0.01% of surface, budget 2%); 7 more within measurement error of the limit |
| thickness distribution | PASS | median 3.13 mm, p95 17.93 mm, max 53.07 mm |
| hollowable at 1.20 mm wall | WARN | 1.05 of 5.17 cm3 (20%) in 1 pocket(s) |
| filament that would save | PASS | 0.16 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (1.3, 15.9, 3.2) | 15 | 0.4 | 2.0 | 0.20 |
| 2 | taper | 0.47 mm | (2.4, 15.6, 3.1) | 2 | 0.1 | 0.1 | 0.46 |
| 3 | taper | 0.47 mm | (-2.4, 15.6, 3.2) | 1 | 0.0 | 0.0 | 0.19 |
| 4 | taper | 0.47 mm | (10.8, 19.1, 0.0) | 1 | 0.0 | 0.0 | 0.18 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
