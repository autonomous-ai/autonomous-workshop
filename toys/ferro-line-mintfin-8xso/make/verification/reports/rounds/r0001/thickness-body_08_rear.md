# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_08_rear.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/rounds/r0001/thickness-body_08_rear.md`

part_body_08_rear.step.py: 0.43 cm3 solid, grid 0.133 mm (107x108x47), 32704 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.2% of surface below (56 of 32704 samples); thinnest 0.13 mm at (6.6, 0.4, 2.0) in 27 region(s); no region is a wall, 27 taper(s) at feature edges (0.21% of surface, budget 2%); 70 more within measurement error of the limit |
| thickness distribution | PASS | median 2.40 mm, p95 5.60 mm, max 5.60 mm |
| hollowable at 1.20 mm wall | PASS | 0.00 of 0.43 cm3 (0%) in 0 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (6.6, 0.4, 2.0) | 12 | 0.3 | 2.7 | 0.09 |
| 2 | taper | 0.20 mm | (3.1, 2.9, 1.8) | 3 | 0.1 | 0.8 | 0.15 |
| 3 | taper | 0.67 mm | (2.3, 3.1, 5.7) | 5 | 0.1 | 0.9 | 0.10 |
| 4 | taper | 0.20 mm | (6.6, -0.8, 1.8) | 5 | 0.1 | 0.9 | 0.11 |
| 5 | taper | 0.27 mm | (2.8, 3.2, 3.4) | 2 | 0.1 | 0.8 | 0.10 |
| 6 | taper | 0.13 mm | (3.4, -3.1, 3.4) | 2 | 0.1 | 0.8 | 0.10 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
