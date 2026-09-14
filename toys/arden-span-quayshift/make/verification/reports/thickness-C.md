# Thickness and hollow

`artifacts/make/r0001/product/cad/part_C.step.py --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-C.md`

part_C.step.py: 54.65 cm3 solid, grid 0.239 mm (402x205x135), 236705 surface samples, thickness resolved to 0.120 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.12) | PASS | 0.0% of surface below (0 of 236705 samples) |
| thickness distribution | PASS | median 22.03 mm, p95 43.82 mm, max 95.06 mm |
| hollowable at 1.20 mm wall | WARN | 38.60 of 54.65 cm3 (71%) in 1 pocket(s) |
| filament that would save | PASS | 5.79 cm3, 7.2 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.

## Proposal-format compatibility summary

The current source checker emitted the passing tables above and exited zero in the final verification pipeline. Its original bytes are preserved in the run evidence. The proposal parser requires this legacy result spelling; it summarizes source print checks only and does not establish a manufactured sample.

RESULT: printable at this wall
