# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_02_front.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/body_02_front/r0003/thickness-body_02_front.md`

part_body_02_front.step.py: 5.77 cm3 solid, grid 0.133 mm (452x334x79), 244738 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | FAIL | 1.0% of surface below (2103 of 244738 samples); thinnest 0.13 mm at (-5.3, 12.7, 0.0) in 16 region(s); 1 wall(s) (widest band 3.05 mm), 15 taper(s) at feature edges (0.02% of surface, budget 2%); 315 more within measurement error of the limit |
| thickness distribution | PASS | median 3.13 mm, p95 15.53 mm, max 59.60 mm |
| hollowable at 1.20 mm wall | WARN | 1.09 of 5.77 cm3 (19%) in 2 pocket(s) |
| filament that would save | PASS | 0.16 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.13 mm | (-5.3, 12.7, 0.0) | 2074 | 41.8 | 13.7 | 3.05 |
| 2 | taper | 0.13 mm | (-3.7, 15.7, 2.6) | 4 | 0.1 | 0.7 | 0.15 |
| 3 | taper | 0.40 mm | (2.1, 21.3, 2.0) | 5 | 0.1 | 1.1 | 0.10 |
| 4 | taper | 0.60 mm | (-3.1, 16.0, 2.6) | 3 | 0.1 | 1.4 | 0.05 |
| 5 | taper | 0.27 mm | (3.2, 21.3, 2.0) | 3 | 0.1 | 0.3 | 0.19 |
| 6 | taper | 0.47 mm | (-6.1, 13.5, 2.9) | 2 | 0.1 | 0.0 | 0.48 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
