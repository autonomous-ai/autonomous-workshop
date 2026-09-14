# Thickness and hollow

`artifacts/make/r0001/product/cad/part_black_queen.step.py --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-black_queen.md`

part_black_queen.step.py: 3.14 cm3 solid, grid 0.133 mm (121x125x215), 90593 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 90593 samples) |
| thickness distribution | PASS | median 11.93 mm, p95 28.00 mm, max 28.00 mm |
| hollowable at 1.20 mm wall | WARN | 1.34 of 3.14 cm3 (43%) in 1 pocket(s) |
| filament that would save | PASS | 0.20 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.

## Recorded tool stdout verdict

RESULT: printable at this wall

Recorded in `measure/rounds/r0001/thickness-black_queen.log` (sha256 0fdbb5c743a75e64a89e7ad9c93979387605dd139d827fbf9a6cfdbd6b3b301d). The final verifier reran the same geometry and returned exit 0; report measurement bodies match.
