# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_02_front.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/body_02_front/r0002/thickness-body_02_front.md`

part_body_02_front.step.py: 5.95 cm3 solid, grid 0.133 mm (452x334x79), 246548 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (5 of 246548 samples); thinnest 0.53 mm at (-15.7, 19.2, 0.0) in 4 region(s); no region is a wall, 4 taper(s) at feature edges (0.00% of surface, budget 2%) |
| thickness distribution | PASS | median 3.13 mm, p95 20.53 mm, max 59.60 mm |
| hollowable at 1.20 mm wall | WARN | 1.14 of 5.95 cm3 (19%) in 2 pocket(s) |
| filament that would save | PASS | 0.17 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.60 mm | (-0.2, 16.7, 3.1) | 2 | 0.0 | 0.1 | 0.33 |
| 2 | taper | 0.53 mm | (-15.7, 19.2, 0.0) | 1 | 0.0 | 0.0 | 0.19 |
| 3 | taper | 0.67 mm | (-1.7, 16.5, 3.1) | 1 | 0.0 | 0.0 | 0.19 |
| 4 | taper | 0.67 mm | (25.4, 11.8, 0.0) | 1 | 0.0 | 0.0 | 0.16 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
