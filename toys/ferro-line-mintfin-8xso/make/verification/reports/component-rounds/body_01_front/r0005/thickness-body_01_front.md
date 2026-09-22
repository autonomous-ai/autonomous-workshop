# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_01_front.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/body_01_front/r0005/thickness-body_01_front.md`

part_body_01_front.step.py: 2.11 cm3 solid, grid 0.133 mm (436x241x82), 170790 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (1 of 170790 samples); thinnest 0.60 mm at (-12.8, -19.9, 0.0) in 1 region(s); no region is a wall, 1 taper(s) at feature edges (0.00% of surface, budget 2%) |
| thickness distribution | PASS | median 1.20 mm, p95 10.73 mm, max 57.47 mm |
| hollowable at 1.20 mm wall | WARN | 0.22 of 2.11 cm3 (11%) in 1 pocket(s) |
| filament that would save | PASS | 0.03 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.60 mm | (-12.8, -19.9, 0.0) | 1 | 0.0 | 0.0 | 0.19 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
