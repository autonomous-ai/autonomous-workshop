# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_sun.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/sun/r0001/thickness-sun.md`

part_sun.step.py: 435.77 cm3 solid, grid 0.390 mm (492x492x48), 377966 surface samples, thickness resolved to 0.195 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.20) | PASS | 0.0% of surface below (553 of 377966 samples); thinnest 0.39 mm at (36.7, 87.6, 16.1) in 16 region(s); no region is a wall, 13 taper(s) at feature edges and 3 spot(s) too small to be a wall (0.04% of surface, budget 2%); 1152 more within measurement error of the limit |
| thickness distribution | PASS | median 16.77 mm, p95 179.81 mm, max 190.14 mm |
| hollowable at 1.20 mm wall | WARN | 361.50 of 435.77 cm3 (83%) in 1 pocket(s) |
| filament that would save | PASS | 54.23 cm3, 67.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.39 mm | (7.5, -59.7, 16.2) | 191 | 7.3 | 10.0 | 0.73 |
| 2 | taper | 0.59 mm | (-8.5, 61.5, 16.5) | 40 | 5.9 | 9.2 | 0.64 |
| 3 | taper | 0.59 mm | (-62.3, -8.6, 16.3) | 37 | 5.8 | 9.3 | 0.62 |
| 4 | taper | 0.39 mm | (59.9, 7.5, 16.5) | 242 | 5.6 | 9.8 | 0.57 |
| 5 | spot | 0.39 mm | (-55.2, 71.1, 16.2) | 1 | 0.8 | 0.0 | 2.13 |
| 6 | spot | 0.59 mm | (-71.1, -55.2, 16.3) | 2 | 0.8 | 0.1 | 2.13 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
