# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_mission_guide.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0004/thickness-mission_guide.md`

part_mission_guide.step.py: 6.56 cm3 solid, grid 0.133 mm (485x121x140), 224629 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (1 of 224629 samples); thinnest 0.73 mm at (-31.4, -2.2, 6.2) in 1 region(s); no region is a wall, 1 taper(s) at feature edges (0.00% of surface, budget 2%); 1 more within measurement error of the limit |
| thickness distribution | PASS | median 5.87 mm, p95 18.00 mm, max 64.00 mm |
| hollowable at 1.20 mm wall | WARN | 2.14 of 6.56 cm3 (33%) in 1 pocket(s) |
| filament that would save | PASS | 0.32 cm3, 0.4 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.73 mm | (-31.4, -2.2, 6.2) | 1 | 0.0 | 0.0 | 0.14 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
