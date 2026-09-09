# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cybercab/measure/rounds/r0004/parts/body.stl --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cybercab/measure/rounds/r0004/thickness-body.md`

<WORKSHOP_RUN>/artifacts/make/r0001/product/cybercab/measure/rounds/r0004/parts/body.stl: 78.92 cm3 solid, grid 0.410 mm (444x195x129), 313682 surface samples, grid resolved to 0.205 mm, exact where under the minimum

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (grid +/-0.20, exact where under) | PASS | 0.0% of surface below (4 of 313682 samples); thinnest 0.19 mm at (0.6, 36.0, 26.6) in 2 region(s); no region is a wall, 2 taper(s) at feature edges (0.00% of surface, budget 2%); 68 grid reading(s) under the limit measured exact on the mesh |
| thickness distribution | PASS | median 3.28 mm, p95 18.02 mm, max 121.22 mm |
| hollowable at 1.20 mm wall | WARN | 15.28 of 78.92 cm3 (19%) in 5 pocket(s) |
| filament that would save | PASS | 2.29 cm3, 2.8 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.30 mm | (179.2, 34.8, 13.3) | 3 | 0.7 | 2.8 | 0.24 |
| 2 | taper | 0.19 mm | (0.6, 36.0, 26.6) | 1 | 0.2 | 0.0 | 0.51 |

Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
