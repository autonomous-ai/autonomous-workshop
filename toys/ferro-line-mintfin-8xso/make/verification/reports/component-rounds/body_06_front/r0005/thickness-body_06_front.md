# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_06_front.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/body_06_front/r0005/thickness-body_06_front.md`

part_body_06_front.step.py: 0.94 cm3 solid, grid 0.133 mm (208x178x78), 70184 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (5 of 70184 samples); thinnest 0.13 mm at (-4.5, 5.4, 0.9) in 2 region(s); no region is a wall, 1 taper(s) at feature edges and 1 spot(s) too small to be a wall (0.03% of surface, budget 2%) |
| thickness distribution | PASS | median 1.20 mm, p95 14.33 mm, max 27.13 mm |
| hollowable at 1.20 mm wall | WARN | 0.15 of 0.94 cm3 (15%) in 1 pocket(s) |
| filament that would save | PASS | 0.02 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (-4.5, 5.4, 0.9) | 3 | 0.2 | 0.8 | 0.29 |
| 2 | spot | 0.13 mm | (4.5, 5.4, 0.8) | 2 | 0.2 | 0.1 | 1.17 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
