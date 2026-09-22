# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_02_front.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/body_02_front/r0005/thickness-body_02_front.md`

part_body_02_front.step.py: 2.62 cm3 solid, grid 0.140 mm (430x318x78), 213534 surface samples, thickness resolved to 0.070 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (4 of 213534 samples); thinnest 0.14 mm at (-5.5, 13.4, 1.0) in 4 region(s); no region is a wall, 3 taper(s) at feature edges and 1 spot(s) too small to be a wall (0.01% of surface, budget 2%); 1 more within measurement error of the limit |
| thickness distribution | PASS | median 1.12 mm, p95 10.01 mm, max 59.57 mm |
| hollowable at 1.20 mm wall | WARN | 0.22 of 2.62 cm3 (9%) in 1 pocket(s) |
| filament that would save | PASS | 0.03 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | spot | 0.14 mm | (-5.5, 13.4, 1.0) | 1 | 0.1 | 0.0 | 1.01 |
| 2 | taper | 0.49 mm | (1.9, -22.5, 1.1) | 1 | 0.0 | 0.0 | 0.18 |
| 3 | taper | 0.42 mm | (16.5, -18.8, 0.0) | 1 | 0.0 | 0.0 | 0.18 |
| 4 | taper | 0.42 mm | (-22.5, 14.8, 0.0) | 1 | 0.0 | 0.0 | 0.17 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
