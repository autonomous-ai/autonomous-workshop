# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_corona_cell.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/corona_cell/r0004/thickness-corona_cell.md`

part_corona_cell.step.py: 3.49 cm3 solid, grid 0.133 mm (262x262x80), 156777 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (3 of 156777 samples); thinnest 0.33 mm at (-15.8, 15.6, 10.0) in 2 region(s); no region is a wall, 2 taper(s) at feature edges (0.00% of surface, budget 2%) |
| thickness distribution | PASS | median 2.93 mm, p95 34.27 mm, max 46.00 mm |
| hollowable at 1.20 mm wall | WARN | 0.42 of 3.49 cm3 (12%) in 1 pocket(s) |
| filament that would save | PASS | 0.06 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.40 mm | (-2.7, 3.6, 3.0) | 1 | 0.0 | 0.0 | 0.13 |
| 2 | taper | 0.33 mm | (-15.8, 15.6, 10.0) | 2 | 0.0 | 0.2 | 0.08 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
