# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_world_uranus_sol.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/world_uranus_sol/r0001/thickness-world_uranus_sol.md`

part_world_uranus_sol.step.py: 9.97 cm3 solid, grid 0.140 mm (246x247x190), 174888 surface samples, thickness resolved to 0.070 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (14 of 174888 samples); thinnest 0.14 mm at (1.1, 3.5, 25.4) in 11 region(s); no region is a wall, 11 taper(s) at feature edges (0.01% of surface, budget 2%); 2 more within measurement error of the limit |
| thickness distribution | PASS | median 21.84 mm, p95 33.39 mm, max 33.74 mm |
| hollowable at 1.20 mm wall | WARN | 6.08 of 9.97 cm3 (61%) in 1 pocket(s) |
| filament that would save | PASS | 0.91 cm3, 1.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.35 mm | (1.5, 9.0, 21.8) | 2 | 0.1 | 0.0 | 0.37 |
| 2 | taper | 0.63 mm | (1.0, 11.4, 17.7) | 2 | 0.1 | 0.0 | 0.37 |
| 3 | taper | 0.63 mm | (-0.6, -8.6, 5.6) | 1 | 0.1 | 0.0 | 0.37 |
| 4 | taper | 0.35 mm | (1.5, -9.0, 21.9) | 2 | 0.0 | 0.1 | 0.33 |
| 5 | taper | 0.28 mm | (1.9, 6.3, 24.1) | 1 | 0.0 | 0.0 | 0.21 |
| 6 | taper | 0.70 mm | (1.1, -0.0, 25.9) | 1 | 0.0 | 0.0 | 0.20 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
