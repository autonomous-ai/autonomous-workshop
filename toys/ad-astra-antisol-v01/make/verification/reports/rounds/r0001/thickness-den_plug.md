# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_den_plug.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/thickness-den_plug.md`

part_den_plug.step.py: 10.15 cm3 solid, grid 0.147 mm (270x260x168), 179311 surface samples, thickness resolved to 0.074 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (1 of 179311 samples); thinnest 0.59 mm at (-18.4, -18.2, 24.0) in 1 region(s); no region is a wall, 1 taper(s) at feature edges (0.00% of surface, budget 2%); 25 more within measurement error of the limit |
| thickness distribution | PASS | median 8.16 mm, p95 33.52 mm, max 44.91 mm |
| hollowable at 1.20 mm wall | WARN | 5.85 of 10.15 cm3 (58%) in 3 pocket(s) |
| filament that would save | PASS | 0.88 cm3, 1.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.59 mm | (-18.4, -18.2, 24.0) | 1 | 0.0 | 0.0 | 0.10 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
