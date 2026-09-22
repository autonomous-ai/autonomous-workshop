# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_drop_a07_beige.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/drop_a07_beige/r0001/thickness-drop_a07_beige.md`

part_drop_a07_beige.step.py: 0.16 cm3 solid, grid 0.133 mm (80x57x39), 10351 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (1 of 10351 samples); thinnest 0.33 mm at (-4.5, 3.4, 0.1) in 1 region(s); no region is a wall, 1 taper(s) at feature edges (0.00% of surface, budget 2%) |
| thickness distribution | PASS | median 4.53 mm, p95 7.47 mm, max 10.87 mm |
| hollowable at 1.20 mm wall | WARN | 0.02 of 0.16 cm3 (12%) in 1 pocket(s), 1 too small to shell |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.33 mm | (-4.5, 3.4, 0.1) | 1 | 0.0 | 0.0 | 0.01 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
