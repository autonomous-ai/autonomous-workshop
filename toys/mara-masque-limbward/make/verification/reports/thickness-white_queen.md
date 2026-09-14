# Thickness and hollow

`artifacts/make/r0001/product/cad/part_white_queen.step.py --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-white_queen.md`

part_white_queen.step.py: 3.23 cm3 solid, grid 0.133 mm (125x125x215), 92835 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 92835 samples) |
| thickness distribution | PASS | median 11.93 mm, p95 28.00 mm, max 28.00 mm |
| hollowable at 1.20 mm wall | WARN | 1.38 of 3.23 cm3 (43%) in 1 pocket(s) |
| filament that would save | PASS | 0.21 cm3, 0.3 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.

## Recorded tool stdout verdict

RESULT: printable at this wall

Recorded in `measure/rounds/r0001/thickness-white_queen.log` (sha256 dc726842d86fc1c448ef4f1dc43d181d76749d94d51953a66450c52a9b7b3380). The final verifier reran the same geometry and returned exit 0; report measurement bodies match.
