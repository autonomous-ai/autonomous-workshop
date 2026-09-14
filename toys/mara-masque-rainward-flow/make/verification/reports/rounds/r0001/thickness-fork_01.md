# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_fork_01.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/thickness-fork_01.md`

part_fork_01.step.py: 0.27 cm3 solid, grid 0.133 mm (95x65x35), 15597 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (6 of 15597 samples); thinnest 0.13 mm at (-3.1, 0.3, 0.0) in 5 region(s); no region is a wall, 5 taper(s) at feature edges (0.05% of surface, budget 2%); 1 more within measurement error of the limit |
| thickness distribution | PASS | median 4.00 mm, p95 10.87 mm, max 12.07 mm |
| hollowable at 1.20 mm wall | WARN | 0.04 of 0.27 cm3 (16%) in 1 pocket(s) |
| filament that would save | PASS | 0.01 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.67 mm | (2.4, 3.9, 0.2) | 2 | 0.0 | 0.1 | 0.28 |
| 2 | taper | 0.40 mm | (1.3, -3.9, 0.0) | 1 | 0.0 | 0.0 | 0.22 |
| 3 | taper | 0.60 mm | (6.0, 0.4, 0.2) | 1 | 0.0 | 0.0 | 0.22 |
| 4 | taper | 0.13 mm | (-3.1, 0.3, 0.0) | 1 | 0.0 | 0.0 | 0.14 |
| 5 | taper | 0.20 mm | (2.2, 4.0, 4.0) | 1 | 0.0 | 0.0 | 0.14 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
