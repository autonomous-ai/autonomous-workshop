# Thickness and hollow

`artifacts/make/r0001/product/cad/veinwake/part_rind.step.py --nozzle 0.4 --report artifacts/make/r0001/product/cad/veinwake/measure/thickness-rind.md`

part_rind.step.py: 142.53 cm3 solid, grid 0.291 mm (486x451x53), 378311 surface samples, thickness resolved to 0.146 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.15) | PASS | 0.0% of surface below (7 of 378311 samples); thinnest 0.29 mm at (53.7, 55.0, 0.1) in 6 region(s); no region is a wall, 5 taper(s) at feature edges and 1 spot(s) too small to be a wall (0.00% of surface, budget 2%) |
| thickness distribution | PASS | median 7.86 mm, p95 83.24 mm, max 154.98 mm |
| hollowable at 1.20 mm wall | WARN | 93.67 of 142.53 cm3 (66%) in 1 pocket(s) |
| filament that would save | PASS | 14.05 cm3, 17.4 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | spot | 0.29 mm | (-53.0, 55.3, 0.0) | 1 | 0.2 | 0.0 | 0.82 |
| 2 | taper | 0.44 mm | (-59.6, 49.4, 0.1) | 2 | 0.2 | 0.0 | 0.74 |
| 3 | taper | 0.58 mm | (-21.4, -32.6, 8.0) | 1 | 0.1 | 0.0 | 0.47 |
| 4 | taper | 0.58 mm | (64.3, 41.7, 0.0) | 1 | 0.1 | 0.0 | 0.39 |
| 5 | taper | 0.29 mm | (53.7, 55.0, 0.1) | 1 | 0.1 | 0.0 | 0.37 |
| 6 | taper | 0.29 mm | (-37.0, 62.6, 0.1) | 1 | 0.1 | 0.0 | 0.37 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
