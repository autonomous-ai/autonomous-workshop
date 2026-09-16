# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_support.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/support/r0001/thickness-support.md`

part_support.step.py: 13.53 cm3 solid, grid 0.321 mm (185x185x307), 106407 surface samples, thickness resolved to 0.160 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.16) | FAIL | 0.2% of surface below (170 of 106407 samples); thinnest 0.32 mm at (-5.5, -4.4, 74.0) in 2 region(s); 1 wall(s) (widest band 1.16 mm), 1 taper(s) at feature edges (0.00% of surface, budget 2%); 158 more within measurement error of the limit |
| thickness distribution | PASS | median 3.85 mm, p95 22.46 mm, max 93.38 mm |
| hollowable at 1.20 mm wall | WARN | 2.86 of 13.53 cm3 (21%) in 1 pocket(s) |
| filament that would save | PASS | 0.43 cm3, 0.5 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.32 mm | (-5.5, -4.4, 74.0) | 169 | 23.5 | 20.3 | 1.16 |
| 2 | taper | 0.32 mm | (5.2, -1.1, 4.0) | 1 | 0.1 | 0.0 | 0.33 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
