# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/part_carrier.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/measure/rounds/r0001/thickness-carrier.md`

part_carrier.step.py: 11.68 cm3 solid, grid 0.354 mm (424x344x71), 79747 surface samples, thickness resolved to 0.177 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.18) | PASS | 0.0% of surface below (82 of 79747 samples); thinnest 0.35 mm at (20.2, 46.6, 13.0) in 20 region(s); no region is a wall, 20 taper(s) at feature edges (0.05% of surface, budget 2%); 40 more within measurement error of the limit |
| thickness distribution | PASS | median 3.18 mm, p95 8.49 mm, max 51.30 mm |
| hollowable at 1.20 mm wall | WARN | 2.09 of 11.68 cm3 (18%) in 1 pocket(s) |
| filament that would save | PASS | 0.31 cm3, 0.4 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.35 mm | (-19.8, -48.4, 13.2) | 10 | 0.8 | 2.4 | 0.32 |
| 2 | taper | 0.35 mm | (37.9, 26.4, 13.2) | 8 | 0.5 | 2.5 | 0.22 |
| 3 | taper | 0.35 mm | (-1.5, -31.4, 23.5) | 6 | 0.5 | 1.7 | 0.28 |
| 4 | taper | 0.35 mm | (-9.9, 56.9, 13.2) | 6 | 0.4 | 2.0 | 0.22 |
| 5 | taper | 0.53 mm | (43.4, -46.3, 13.5) | 5 | 0.4 | 1.0 | 0.37 |
| 6 | taper | 0.35 mm | (20.2, 46.6, 13.0) | 6 | 0.3 | 1.9 | 0.16 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
