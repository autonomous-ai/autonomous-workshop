# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_leg_left.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/rounds/r0002/thickness-leg_left.md`

part_leg_left.step.py: 5.18 cm3 solid, grid 0.133 mm (211x158x147), 97699 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (33 of 97699 samples); thinnest 0.13 mm at (11.9, 9.4, 19.0) in 3 region(s); no region is a wall, 3 taper(s) at feature edges (0.04% of surface, budget 2%); 15 more within measurement error of the limit |
| thickness distribution | PASS | median 14.40 mm, p95 23.80 mm, max 24.13 mm |
| hollowable at 1.20 mm wall | WARN | 3.28 of 5.18 cm3 (63%) in 1 pocket(s) |
| filament that would save | PASS | 0.49 cm3, 0.6 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (11.9, 9.4, 19.0) | 18 | 0.4 | 1.6 | 0.26 |
| 2 | taper | 0.13 mm | (9.0, 11.5, 19.0) | 12 | 0.2 | 1.4 | 0.17 |
| 3 | taper | 0.53 mm | (10.8, 10.5, 19.0) | 3 | 0.1 | 0.5 | 0.10 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
