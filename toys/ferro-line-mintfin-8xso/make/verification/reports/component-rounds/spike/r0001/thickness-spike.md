# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_spike.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/spike/r0001/thickness-spike.md`

part_spike.step.py: 0.29 cm3 solid, grid 0.133 mm (65x65x95), 14170 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 1.4% of surface below (192 of 14170 samples); thinnest 0.13 mm at (-1.9, -3.5, 0.0) in 5 region(s); no region is a wall, 5 taper(s) at feature edges (1.39% of surface, budget 2%); 55 more within measurement error of the limit |
| thickness distribution | PASS | median 6.27 mm, p95 8.40 mm, max 12.00 mm |
| hollowable at 1.20 mm wall | WARN | 0.07 of 0.29 cm3 (25%) in 1 pocket(s) |
| filament that would save | PASS | 0.01 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (-1.9, -3.5, 0.0) | 181 | 3.3 | 10.8 | 0.31 |
| 2 | taper | 0.53 mm | (-1.3, 3.8, 0.0) | 4 | 0.1 | 1.1 | 0.06 |
| 3 | taper | 0.13 mm | (-0.3, 3.9, 0.0) | 3 | 0.1 | 0.3 | 0.15 |
| 4 | taper | 0.13 mm | (1.1, 3.8, 0.0) | 3 | 0.0 | 0.4 | 0.13 |
| 5 | taper | 0.13 mm | (-3.1, 2.5, 0.0) | 1 | 0.0 | 0.0 | 0.23 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
