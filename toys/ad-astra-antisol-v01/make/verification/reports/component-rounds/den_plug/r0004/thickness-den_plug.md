# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_den_plug.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/den_plug/r0004/thickness-den_plug.md`

part_den_plug.step.py: 9.98 cm3 solid, grid 0.147 mm (270x260x168), 179511 surface samples, thickness resolved to 0.074 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (8 of 179511 samples); thinnest 0.15 mm at (-18.6, -18.2, 24.0) in 2 region(s); no region is a wall, 2 taper(s) at feature edges (0.00% of surface, budget 2%); 29 more within measurement error of the limit |
| thickness distribution | PASS | median 7.79 mm, p95 34.32 mm, max 45.42 mm |
| hollowable at 1.20 mm wall | WARN | 5.69 of 9.98 cm3 (57%) in 3 pocket(s), 1 too small to shell |
| filament that would save | PASS | 0.85 cm3, 1.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.29 mm | (18.5, -18.2, 24.0) | 6 | 0.1 | 0.8 | 0.15 |
| 2 | taper | 0.15 mm | (-18.6, -18.2, 24.0) | 2 | 0.0 | 0.3 | 0.12 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
