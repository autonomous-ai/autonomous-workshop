# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/veinwake/part_rind.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/veinwake/measure/rounds/r0003/thickness-rind.md`

part_rind.step.py: 142.52 cm3 solid, grid 0.291 mm (486x451x53), 378584 surface samples, thickness resolved to 0.146 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.15) | PASS | 0.0% of surface below (3 of 378584 samples); thinnest 0.29 mm at (-53.1, 55.3, 0.0) in 3 region(s); no region is a wall, 3 taper(s) at feature edges (0.00% of surface, budget 2%) |
| thickness distribution | PASS | median 7.86 mm, p95 84.67 mm, max 154.98 mm |
| hollowable at 1.20 mm wall | WARN | 93.66 of 142.52 cm3 (66%) in 1 pocket(s) |
| filament that would save | PASS | 14.05 cm3, 17.4 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.29 mm | (-53.1, 55.3, 0.0) | 1 | 0.2 | 0.0 | 0.64 |
| 2 | taper | 0.58 mm | (-59.4, -13.2, 14.0) | 1 | 0.1 | 0.0 | 0.38 |
| 3 | taper | 0.58 mm | (-64.5, -42.4, 0.1) | 1 | 0.1 | 0.0 | 0.37 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
