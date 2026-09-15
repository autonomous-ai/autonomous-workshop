# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_launcher_band_guard.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0005/thickness-launcher_band_guard.md`

part_launcher_band_guard.step.py: 9.47 cm3 solid, grid 0.162 mm (164x866x74), 279437 surface samples, thickness resolved to 0.081 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.08) | PASS | 0.0% of surface below (34 of 279437 samples); thinnest 0.65 mm at (10.1, 133.7, 3.0) in 10 region(s); no region is a wall, 10 taper(s) at feature edges (0.01% of surface, budget 2%) |
| thickness distribution | PASS | median 2.92 mm, p95 23.99 mm, max 131.92 mm |
| hollowable at 1.20 mm wall | WARN | 1.83 of 9.47 cm3 (19%) in 1 pocket(s) |
| filament that would save | PASS | 0.27 cm3, 0.3 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.65 mm | (20.8, 7.8, 3.0) | 8 | 0.2 | 3.4 | 0.07 |
| 2 | taper | 0.65 mm | (16.4, 6.0, 3.0) | 5 | 0.1 | 1.4 | 0.10 |
| 3 | taper | 0.65 mm | (11.1, 130.0, 3.0) | 5 | 0.1 | 1.4 | 0.09 |
| 4 | taper | 0.65 mm | (17.5, 9.4, 3.0) | 5 | 0.1 | 0.8 | 0.16 |
| 5 | taper | 0.65 mm | (10.1, 133.7, 3.0) | 4 | 0.1 | 1.4 | 0.08 |
| 6 | taper | 0.65 mm | (14.3, 133.1, 3.0) | 2 | 0.1 | 0.8 | 0.07 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
