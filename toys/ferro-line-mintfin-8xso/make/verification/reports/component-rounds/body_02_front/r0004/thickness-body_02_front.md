# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_02_front.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/body_02_front/r0004/thickness-body_02_front.md`

part_body_02_front.step.py: 2.76 cm3 solid, grid 0.133 mm (452x334x79), 234750 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (3 of 234750 samples); thinnest 0.13 mm at (5.7, 13.4, 1.0) in 2 region(s); no region is a wall, 2 taper(s) at feature edges (0.01% of surface, budget 2%) |
| thickness distribution | PASS | median 1.20 mm, p95 10.00 mm, max 59.60 mm |
| hollowable at 1.20 mm wall | WARN | 0.22 of 2.76 cm3 (8%) in 1 pocket(s) |
| filament that would save | PASS | 0.03 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (5.7, 13.4, 1.0) | 2 | 0.2 | 0.9 | 0.27 |
| 2 | taper | 0.47 mm | (7.0, -21.8, 1.2) | 1 | 0.0 | 0.0 | 0.13 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
