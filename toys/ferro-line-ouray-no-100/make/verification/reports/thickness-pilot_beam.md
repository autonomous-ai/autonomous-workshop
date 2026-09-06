# Thickness and hollow

`artifacts/make/r0001/product/cad-project/part_pilot_beam.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad-project/measure/thickness-pilot_beam.md`

artifacts/make/r0001/product/cad-project/part_pilot_beam.stl: 1.36 cm3 solid, grid 0.133 mm (249x80x249), 116843 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (22 of 116843 samples); thinnest 0.13 mm at (-3.2, -3.4, 12.4) in 18 region(s); no region is a wall, 18 taper(s) at feature edges (0.02% of surface, budget 2%) |
| thickness distribution | PASS | median 1.20 mm, p95 17.00 mm, max 30.00 mm |
| hollowable at 1.20 mm wall | WARN | 0.07 of 1.36 cm3 (5%) in 1 pocket(s), 7 too small to shell |
| filament that would save | PASS | 0.01 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.20 mm | (-7.4, -3.3, 8.0) | 3 | 0.1 | 0.2 | 0.38 |
| 2 | taper | 0.13 mm | (-10.3, -3.3, 5.1) | 2 | 0.0 | 0.2 | 0.23 |
| 3 | taper | 0.13 mm | (-0.0, -3.5, 16.0) | 2 | 0.0 | 0.5 | 0.09 |
| 4 | taper | 0.13 mm | (-3.2, -3.4, 12.4) | 1 | 0.0 | 0.0 | 0.18 |
| 5 | taper | 0.20 mm | (3.2, -3.3, 18.7) | 1 | 0.0 | 0.0 | 0.18 |
| 6 | taper | 0.20 mm | (-16.7, -9.4, 11.5) | 1 | 0.0 | 0.0 | 0.18 |

Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
