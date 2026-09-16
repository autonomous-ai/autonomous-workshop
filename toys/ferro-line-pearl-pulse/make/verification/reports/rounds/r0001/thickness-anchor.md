# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_anchor.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/thickness-anchor.md`

part_anchor.step.py: 0.40 cm3 solid, grid 0.133 mm (86x86x96), 22043 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.2% of surface below (41 of 22043 samples); thinnest 0.13 mm at (1.0, -1.2, 10.1) in 2 region(s); no region is a wall, 2 taper(s) at feature edges (0.20% of surface, budget 2%); 5 more within measurement error of the limit |
| thickness distribution | PASS | median 6.73 mm, p95 10.73 mm, max 11.87 mm |
| hollowable at 1.20 mm wall | WARN | 0.07 of 0.40 cm3 (19%) in 1 pocket(s) |
| filament that would save | PASS | 0.01 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (1.0, -1.2, 10.1) | 40 | 0.8 | 1.8 | 0.47 |
| 2 | taper | 0.67 mm | (-0.0, -1.8, 12.2) | 1 | 0.0 | 0.0 | 0.16 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
