# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_01_front.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/body_01_front/r0004/thickness-body_01_front.md`

part_body_01_front.step.py: 3.89 cm3 solid, grid 0.133 mm (436x241x82), 178650 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | FAIL | 6.1% of surface below (11039 of 178650 samples); thinnest 0.13 mm at (-0.7, 8.0, 0.4) in 4 region(s); 1 wall(s) (widest band 3.64 mm), 3 taper(s) at feature edges (0.00% of surface, budget 2%); 1745 more within measurement error of the limit |
| thickness distribution | PASS | median 3.13 mm, p95 11.60 mm, max 57.47 mm |
| hollowable at 1.20 mm wall | WARN | 0.73 of 3.89 cm3 (19%) in 2 pocket(s) |
| filament that would save | PASS | 0.11 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.13 mm | (-0.7, 8.0, 0.4) | 11036 | 196.7 | 54.1 | 3.64 |
| 2 | taper | 0.53 mm | (-3.9, -2.2, 3.2) | 1 | 0.1 | 0.0 | 0.60 |
| 3 | taper | 0.60 mm | (6.5, 0.2, 3.1) | 1 | 0.0 | 0.0 | 0.10 |
| 4 | taper | 0.33 mm | (-6.4, 0.0, 3.2) | 1 | 0.0 | 0.0 | 0.10 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
