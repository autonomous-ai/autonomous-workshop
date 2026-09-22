# Thickness and hollow

`artifacts/make/r0001/product/cad/part_fork_06.step.py --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-fork_06.md`

part_fork_06.step.py: 0.25 cm3 solid, grid 0.133 mm (95x65x35), 14369 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (2 of 14369 samples); thinnest 0.53 mm at (1.8, -3.8, 0.1) in 1 region(s); no region is a wall, 1 taper(s) at feature edges (0.02% of surface, budget 2%); 2 more within measurement error of the limit |
| thickness distribution | PASS | median 4.00 mm, p95 10.67 mm, max 12.93 mm |
| hollowable at 1.20 mm wall | WARN | 0.04 of 0.25 cm3 (16%) in 1 pocket(s) |
| filament that would save | PASS | 0.01 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.53 mm | (1.8, -3.8, 0.1) | 2 | 0.0 | 1.0 | 0.04 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.

## Captured console verdict

The matching current-run check printed the following result. Its measured report content is identical to this final report; only command paths differ. Source: `rounds/r0001/thickness-fork_06.log` (SHA256 `6c81275201438973847944fd8eaa89f726bf1c826ca7790ffc067cdca1f500d1`).

RESULT: printable at this wall
