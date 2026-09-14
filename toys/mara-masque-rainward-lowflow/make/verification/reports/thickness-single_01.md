# Thickness and hollow

`artifacts/make/r0001/product/cad/part_single_01.step.py --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-single_01.md`

part_single_01.step.py: 0.20 cm3 solid, grid 0.133 mm (95x65x35), 12009 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.1% of surface below (8 of 12009 samples); thinnest 0.13 mm at (-5.2, 3.9, 0.0) in 5 region(s); no region is a wall, 5 taper(s) at feature edges (0.06% of surface, budget 2%) |
| thickness distribution | PASS | median 4.00 mm, p95 8.07 mm, max 12.93 mm |
| hollowable at 1.20 mm wall | WARN | 0.03 of 0.20 cm3 (13%) in 1 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.60 mm | (1.5, -3.6, 3.9) | 2 | 0.0 | 0.0 | 0.32 |
| 2 | taper | 0.40 mm | (1.4, -3.5, 0.1) | 2 | 0.0 | 0.2 | 0.25 |
| 3 | taper | 0.13 mm | (-5.2, 3.9, 0.0) | 2 | 0.0 | 0.1 | 0.15 |
| 4 | taper | 0.13 mm | (4.9, 1.3, 0.0) | 1 | 0.0 | 0.0 | 0.13 |
| 5 | taper | 0.13 mm | (5.9, -0.8, 0.0) | 1 | 0.0 | 0.0 | 0.13 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.

## Captured console verdict

The matching current-run check printed the following result. Its measured report content is identical to this final report; only command paths differ. Source: `rounds/r0001/thickness-single_01.log` (SHA256 `286e97ac55f3b63247287d13b6d72ce0ef0dbc24c8a794edf672ed7bb7969304`).

RESULT: printable at this wall
