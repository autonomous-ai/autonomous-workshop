# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_access_cap.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0009/thickness-access_cap.md`

part_access_cap.step.py: 18.47 cm3 solid, grid 0.197 mm (816x735x20), 370848 surface samples, thickness resolved to 0.098 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.10) | PASS | 0.0% of surface below (74 of 370848 samples); thinnest 0.39 mm at (79.6, 5.6, 0.0) in 16 region(s); no region is a wall, 16 taper(s) at feature edges (0.02% of surface, budget 2%); 288 more within measurement error of the limit |
| thickness distribution | PASS | median 2.95 mm, p95 20.39 mm, max 159.76 mm |
| hollowable at 1.20 mm wall | WARN | 2.64 of 18.47 cm3 (14%) in 1 pocket(s) |
| filament that would save | PASS | 0.40 cm3, 0.5 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.59 mm | (6.0, 70.2, 0.0) | 12 | 0.6 | 3.8 | 0.15 |
| 2 | taper | 0.39 mm | (79.6, 5.6, 0.0) | 10 | 0.5 | 3.4 | 0.14 |
| 3 | taper | 0.59 mm | (149.8, 73.3, 0.0) | 10 | 0.5 | 4.8 | 0.10 |
| 4 | taper | 0.59 mm | (78.1, 134.3, 0.0) | 8 | 0.4 | 4.3 | 0.08 |
| 5 | taper | 0.59 mm | (150.8, 69.6, 0.0) | 7 | 0.3 | 3.3 | 0.09 |
| 6 | taper | 0.59 mm | (80.6, 138.3, 0.0) | 6 | 0.3 | 1.1 | 0.24 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
