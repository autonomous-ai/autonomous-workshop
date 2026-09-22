# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_01_front.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/body_01_front/r0009/thickness-body_01_front.md`

part_body_01_front.step.py: 2.53 cm3 solid, grid 0.133 mm (436x293x82), 212953 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (6 of 212953 samples); thinnest 0.13 mm at (-28.7, -1.6, 0.0) in 4 region(s); no region is a wall, 3 taper(s) at feature edges and 1 spot(s) too small to be a wall (0.01% of surface, budget 2%) |
| thickness distribution | PASS | median 1.20 mm, p95 10.33 mm, max 57.47 mm |
| hollowable at 1.20 mm wall | WARN | 0.22 of 2.53 cm3 (9%) in 1 pocket(s) |
| filament that would save | PASS | 0.03 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | spot | 0.20 mm | (-6.0, 7.7, 0.2) | 2 | 0.1 | 0.0 | 0.87 |
| 2 | taper | 0.13 mm | (-3.9, 9.7, 0.6) | 2 | 0.0 | 0.2 | 0.20 |
| 3 | taper | 0.13 mm | (9.6, -20.9, 0.0) | 1 | 0.0 | 0.0 | 0.17 |
| 4 | taper | 0.13 mm | (-28.7, -1.6, 0.0) | 1 | 0.0 | 0.0 | 0.16 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
