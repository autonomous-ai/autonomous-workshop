# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_world_uranus_anti.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/thickness-world_uranus_anti.md`

part_world_uranus_anti.step.py: 9.97 cm3 solid, grid 0.140 mm (247x248x190), 175538 surface samples, thickness resolved to 0.070 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.1% of surface below (189 of 175538 samples); thinnest 0.14 mm at (-2.1, 16.9, 0.0) in 55 region(s); no region is a wall, 55 taper(s) at feature edges (0.14% of surface, budget 2%); 3 more within measurement error of the limit |
| thickness distribution | PASS | median 21.84 mm, p95 33.46 mm, max 33.81 mm |
| hollowable at 1.20 mm wall | WARN | 6.08 of 9.97 cm3 (61%) in 1 pocket(s) |
| filament that would save | PASS | 0.91 cm3, 1.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.14 mm | (-10.3, 13.4, 0.0) | 10 | 0.4 | 2.6 | 0.14 |
| 2 | taper | 0.14 mm | (-16.5, -4.2, 0.0) | 16 | 0.3 | 3.2 | 0.10 |
| 3 | taper | 0.21 mm | (0.7, 8.9, 5.3) | 6 | 0.3 | 0.5 | 0.50 |
| 4 | taper | 0.14 mm | (15.3, -7.2, 0.0) | 13 | 0.3 | 3.6 | 0.07 |
| 5 | taper | 0.28 mm | (8.3, 14.7, 0.0) | 6 | 0.2 | 1.1 | 0.20 |
| 6 | taper | 0.14 mm | (-2.1, 16.9, 0.0) | 8 | 0.2 | 1.4 | 0.15 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
