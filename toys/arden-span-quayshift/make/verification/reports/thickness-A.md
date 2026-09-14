# Thickness and hollow

`artifacts/make/r0001/product/cad/part_A.step.py --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-A.md`

part_A.step.py: 88.11 cm3 solid, grid 0.277 mm (348x272x117), 249291 surface samples, thickness resolved to 0.139 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.14) | PASS | 0.0% of surface below (0 of 249291 samples) |
| thickness distribution | PASS | median 21.90 mm, p95 69.85 mm, max 95.08 mm |
| hollowable at 1.20 mm wall | WARN | 66.59 of 88.11 cm3 (76%) in 1 pocket(s) |
| filament that would save | PASS | 9.99 cm3, 12.4 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.

## Proposal-format compatibility summary

The current source checker emitted the passing tables above and exited zero in the final verification pipeline. Its original bytes are preserved in the run evidence. The proposal parser requires this legacy result spelling; it summarizes source print checks only and does not establish a manufactured sample.

RESULT: printable at this wall
