# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_world_saturn_anti.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0002/thickness-world_saturn_anti.md`

part_world_saturn_anti.step.py: 14.14 cm3 solid, grid 0.147 mm (236x236x202), 187102 surface samples, thickness resolved to 0.074 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.1% of surface below (153 of 187102 samples); thinnest 0.15 mm at (-13.5, 10.3, 0.0) in 51 region(s); no region is a wall, 49 taper(s) at feature edges and 2 spot(s) too small to be a wall (0.13% of surface, budget 2%); 39 more within measurement error of the limit |
| thickness distribution | PASS | median 25.80 mm, p95 33.52 mm, max 34.62 mm |
| hollowable at 1.20 mm wall | WARN | 9.54 of 14.14 cm3 (67%) in 1 pocket(s) |
| filament that would save | PASS | 1.43 cm3, 1.8 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.15 mm | (-13.5, 10.3, 0.0) | 21 | 0.5 | 6.8 | 0.07 |
| 2 | taper | 0.15 mm | (13.6, -1.9, 22.5) | 5 | 0.3 | 1.6 | 0.19 |
| 3 | taper | 0.15 mm | (7.4, -15.3, 0.0) | 8 | 0.3 | 1.6 | 0.16 |
| 4 | taper | 0.15 mm | (13.0, 4.8, 22.2) | 2 | 0.2 | 1.0 | 0.25 |
| 5 | taper | 0.15 mm | (5.6, -16.0, 0.0) | 11 | 0.2 | 2.0 | 0.12 |
| 6 | taper | 0.22 mm | (12.1, -6.9, 21.7) | 2 | 0.2 | 0.5 | 0.44 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
