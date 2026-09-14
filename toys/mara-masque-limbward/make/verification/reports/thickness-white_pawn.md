# Thickness and hollow

`artifacts/make/r0001/product/cad/part_white_pawn.step.py --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-white_pawn.md`

part_white_pawn.step.py: 1.28 cm3 solid, grid 0.133 mm (125x125x95), 43869 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.6% of surface below (272 of 43869 samples); thinnest 0.33 mm at (3.4, 4.0, 11.9) in 1 region(s); no region is a wall, 1 taper(s) at feature edges (0.62% of surface, budget 2%); 16 more within measurement error of the limit |
| thickness distribution | PASS | median 8.93 mm, p95 16.00 mm, max 16.07 mm |
| hollowable at 1.20 mm wall | WARN | 0.48 of 1.28 cm3 (38%) in 1 pocket(s) |
| filament that would save | PASS | 0.07 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.33 mm | (3.4, 4.0, 11.9) | 272 | 5.2 | 9.7 | 0.53 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.

## Recorded tool stdout verdict

RESULT: printable at this wall

Recorded in `measure/rounds/r0001/thickness-white_pawn.log` (sha256 220ae9192926ee5c8192f227a20ebb98c73330658db2310a0f5fee1bc45e1d40). The final verifier reran the same geometry and returned exit 0; report measurement bodies match.
