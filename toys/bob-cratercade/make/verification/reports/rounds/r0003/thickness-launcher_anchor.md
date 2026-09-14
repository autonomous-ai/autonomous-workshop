# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_launcher_anchor.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0003/thickness-launcher_anchor.md`

part_launcher_anchor.step.py: 1.59 cm3 solid, grid 0.133 mm (110x155x125), 65378 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.1% of surface below (51 of 65378 samples); thinnest 0.53 mm at (7.4, 0.0, 3.8) in 1 region(s); no region is a wall, 1 taper(s) at feature edges (0.08% of surface, budget 2%); 35 more within measurement error of the limit |
| thickness distribution | PASS | median 5.93 mm, p95 16.00 mm, max 20.00 mm |
| hollowable at 1.20 mm wall | WARN | 0.45 of 1.59 cm3 (28%) in 1 pocket(s) |
| filament that would save | PASS | 0.07 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.53 mm | (7.4, 0.0, 3.8) | 51 | 1.0 | 2.5 | 0.41 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
