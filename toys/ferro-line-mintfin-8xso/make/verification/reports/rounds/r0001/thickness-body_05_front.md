# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_05_front.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/rounds/r0001/thickness-body_05_front.md`

part_body_05_front.step.py: 1.46 cm3 solid, grid 0.133 mm (276x232x86), 117160 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.2% of surface below (145 of 117160 samples); thinnest 0.13 mm at (-4.3, 9.0, 0.5) in 5 region(s); no region is a wall, 3 taper(s) at feature edges and 2 spot(s) too small to be a wall (0.16% of surface, budget 2%) |
| thickness distribution | PASS | median 1.20 mm, p95 11.20 mm, max 36.20 mm |
| hollowable at 1.20 mm wall | WARN | 0.17 of 1.46 cm3 (11%) in 1 pocket(s) |
| filament that would save | PASS | 0.03 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | spot | 0.13 mm | (1.3, 10.7, 0.6) | 90 | 1.9 | 1.3 | 1.50 |
| 2 | spot | 0.13 mm | (-1.4, 10.7, 0.8) | 46 | 1.2 | 1.2 | 0.96 |
| 3 | taper | 0.20 mm | (4.4, 9.1, 0.2) | 3 | 0.2 | 0.5 | 0.42 |
| 4 | taper | 0.13 mm | (-4.3, 9.0, 0.5) | 5 | 0.2 | 0.6 | 0.29 |
| 5 | taper | 0.60 mm | (7.8, -14.2, 0.0) | 1 | 0.0 | 0.0 | 0.17 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
