# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_05_front.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/body_05_front/r0002/thickness-body_05_front.md`

part_body_05_front.step.py: 3.04 cm3 solid, grid 0.133 mm (276x232x82), 120882 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.1% of surface below (102 of 120882 samples); thinnest 0.20 mm at (-1.1, 12.2, 3.4) in 1 region(s); no region is a wall, 1 taper(s) at feature edges (0.11% of surface, budget 2%); 11 more within measurement error of the limit |
| thickness distribution | PASS | median 3.47 mm, p95 29.93 mm, max 36.20 mm |
| hollowable at 1.20 mm wall | WARN | 0.72 of 3.04 cm3 (24%) in 1 pocket(s) |
| filament that would save | PASS | 0.11 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.20 mm | (-1.1, 12.2, 3.4) | 102 | 2.5 | 8.3 | 0.30 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
