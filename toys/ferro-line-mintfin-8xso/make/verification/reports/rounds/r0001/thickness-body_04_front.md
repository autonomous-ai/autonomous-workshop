# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_04_front.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/rounds/r0001/thickness-body_04_front.md`

part_body_04_front.step.py: 2.10 cm3 solid, grid 0.133 mm (356x293x81), 176398 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (1 of 176398 samples); thinnest 0.20 mm at (-4.5, 12.6, 0.2) in 1 region(s); no region is a wall, 0 taper(s) at feature edges and 1 spot(s) too small to be a wall (0.01% of surface, budget 2%) |
| thickness distribution | PASS | median 1.20 mm, p95 10.00 mm, max 46.87 mm |
| hollowable at 1.20 mm wall | WARN | 0.18 of 2.10 cm3 (9%) in 1 pocket(s) |
| filament that would save | PASS | 0.03 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | spot | 0.20 mm | (-4.5, 12.6, 0.2) | 1 | 0.2 | 0.0 | 1.32 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
