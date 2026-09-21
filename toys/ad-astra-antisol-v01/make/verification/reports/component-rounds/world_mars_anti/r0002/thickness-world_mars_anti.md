# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_world_mars_anti.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/world_mars_anti/r0002/thickness-world_mars_anti.md`

part_world_mars_anti.step.py: 5.91 cm3 solid, grid 0.133 mm (259x260x138), 154018 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.1% of surface below (143 of 154018 samples); thinnest 0.13 mm at (-2.1, 16.9, 0.0) in 41 region(s); no region is a wall, 40 taper(s) at feature edges and 1 spot(s) too small to be a wall (0.11% of surface, budget 2%); 55 more within measurement error of the limit |
| thickness distribution | PASS | median 4.93 mm, p95 33.53 mm, max 33.87 mm |
| hollowable at 1.20 mm wall | WARN | 2.93 of 5.91 cm3 (50%) in 1 pocket(s) |
| filament that would save | PASS | 0.44 cm3, 0.5 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (-2.1, 16.9, 0.0) | 12 | 0.3 | 2.2 | 0.12 |
| 2 | taper | 0.13 mm | (-10.0, 13.8, 0.0) | 13 | 0.2 | 4.7 | 0.05 |
| 3 | taper | 0.27 mm | (15.1, 7.6, 0.0) | 8 | 0.2 | 2.6 | 0.07 |
| 4 | taper | 0.13 mm | (-10.1, -13.5, 0.0) | 6 | 0.2 | 1.4 | 0.13 |
| 5 | taper | 0.13 mm | (-15.1, -7.7, 0.0) | 5 | 0.1 | 1.8 | 0.07 |
| 6 | taper | 0.40 mm | (13.8, -9.8, 0.0) | 7 | 0.1 | 2.9 | 0.04 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
