# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_04_front.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/body_04_front/r0002/thickness-body_04_front.md`

part_body_04_front.step.py: 4.42 cm3 solid, grid 0.133 mm (356x293x81), 181478 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (37 of 181478 samples); thinnest 0.20 mm at (2.1, 15.0, 3.2) in 1 region(s); no region is a wall, 1 taper(s) at feature edges (0.03% of surface, budget 2%); 13 more within measurement error of the limit |
| thickness distribution | PASS | median 3.13 mm, p95 15.53 mm, max 46.87 mm |
| hollowable at 1.20 mm wall | WARN | 0.86 of 4.42 cm3 (19%) in 1 pocket(s) |
| filament that would save | PASS | 0.13 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.20 mm | (2.1, 15.0, 3.2) | 37 | 0.9 | 5.9 | 0.15 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
