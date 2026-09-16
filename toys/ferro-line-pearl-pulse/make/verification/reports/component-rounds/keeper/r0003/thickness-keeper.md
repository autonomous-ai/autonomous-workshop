# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_keeper.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/keeper/r0003/thickness-keeper.md`

part_keeper.step.py: 0.75 cm3 solid, grid 0.133 mm (382x382x14), 84966 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.2% of surface below (149 of 84966 samples); thinnest 0.13 mm at (-18.5, 15.5, 0.4) in 10 region(s); no region is a wall, 8 taper(s) at feature edges and 2 spot(s) too small to be a wall (0.21% of surface, budget 2%); 22 more within measurement error of the limit |
| thickness distribution | PASS | median 1.20 mm, p95 5.00 mm, max 28.33 mm |
| hollowable at 1.20 mm wall | PASS | 0.00 of 0.75 cm3 (0%) in 0 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | spot | 0.40 mm | (-1.2, -25.0, 0.2) | 86 | 2.0 | 1.5 | 1.35 |
| 2 | spot | 0.13 mm | (-18.5, 15.5, 0.4) | 51 | 1.2 | 1.1 | 1.06 |
| 3 | taper | 0.60 mm | (19.3, -16.2, 0.9) | 2 | 0.1 | 0.3 | 0.25 |
| 4 | taper | 0.60 mm | (25.1, 2.1, 0.4) | 2 | 0.1 | 0.2 | 0.28 |
| 5 | taper | 0.73 mm | (7.2, 24.1, 0.7) | 2 | 0.0 | 0.2 | 0.20 |
| 6 | taper | 0.73 mm | (-25.2, 1.3, 0.8) | 2 | 0.0 | 0.8 | 0.06 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
