# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_hopper_funnel.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0009/thickness-hopper_funnel.md`

part_hopper_funnel.step.py: 13.06 cm3 solid, grid 0.197 mm (208x187x279), 307980 surface samples, thickness resolved to 0.098 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.10) | PASS | 0.0% of surface below (7 of 307980 samples); thinnest 0.20 mm at (39.9, 17.6, 0.0) in 3 region(s); no region is a wall, 3 taper(s) at feature edges (0.00% of surface, budget 2%); 10 more within measurement error of the limit |
| thickness distribution | PASS | median 1.97 mm, p95 6.80 mm, max 29.25 mm |
| hollowable at 1.20 mm wall | WARN | 0.88 of 13.06 cm3 (7%) in 1 pocket(s), 15 too small to shell |
| filament that would save | PASS | 0.13 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.20 mm | (39.9, 17.6, 0.0) | 3 | 0.1 | 1.0 | 0.15 |
| 2 | taper | 0.39 mm | (0.0, 35.9, 0.1) | 3 | 0.1 | 0.1 | 0.59 |
| 3 | taper | 0.30 mm | (0.0, 0.2, 0.1) | 1 | 0.0 | 0.0 | 0.20 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
