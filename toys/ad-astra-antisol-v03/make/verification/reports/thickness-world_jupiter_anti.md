# Thickness and hollow

`artifacts/make/r0001/product/cad/part_world_jupiter_anti.step.py --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-world_jupiter_anti.md`

part_world_jupiter_anti.step.py: 14.65 cm3 solid, grid 0.147 mm (236x236x209), 184079 surface samples, thickness resolved to 0.074 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.1% of surface below (123 of 184079 samples); thinnest 0.15 mm at (-13.5, 10.3, 0.0) in 37 region(s); no region is a wall, 37 taper(s) at feature edges (0.08% of surface, budget 2%); 46 more within measurement error of the limit |
| thickness distribution | PASS | median 26.83 mm, p95 33.59 mm, max 35.87 mm |
| hollowable at 1.20 mm wall | WARN | 10.19 of 14.65 cm3 (70%) in 1 pocket(s) |
| filament that would save | PASS | 1.53 cm3, 1.9 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.15 mm | (-16.1, -5.2, 0.0) | 15 | 0.3 | 4.1 | 0.08 |
| 2 | taper | 0.15 mm | (-10.3, 13.3, 0.0) | 10 | 0.3 | 3.2 | 0.09 |
| 3 | taper | 0.15 mm | (15.3, 7.3, 0.0) | 6 | 0.2 | 3.0 | 0.08 |
| 4 | taper | 0.44 mm | (-11.1, -12.8, 0.0) | 5 | 0.2 | 0.3 | 0.61 |
| 5 | taper | 0.15 mm | (5.7, -15.9, 0.0) | 7 | 0.2 | 1.6 | 0.11 |
| 6 | taper | 0.15 mm | (-7.6, 15.1, 0.0) | 7 | 0.2 | 2.0 | 0.08 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
