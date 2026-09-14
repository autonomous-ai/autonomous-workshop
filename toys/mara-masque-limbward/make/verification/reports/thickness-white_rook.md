# Thickness and hollow

`artifacts/make/r0001/product/cad/part_white_rook.step.py --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-white_rook.md`

part_white_rook.step.py: 2.73 cm3 solid, grid 0.133 mm (125x125x260), 107019 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 107019 samples) |
| thickness distribution | PASS | median 3.00 mm, p95 33.93 mm, max 34.00 mm |
| hollowable at 1.20 mm wall | WARN | 0.65 of 2.73 cm3 (24%) in 1 pocket(s) |
| filament that would save | PASS | 0.10 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.

## Recorded tool stdout verdict

RESULT: printable at this wall

Recorded in `measure/rounds/r0001/thickness-white_rook.log` (sha256 f4aeffe78c8cf9b764db55cd2e4d8221ca0e6892bee814b4c4f390818093ce2a). The final verifier reran the same geometry and returned exit 0; report measurement bodies match.
