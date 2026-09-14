# Thickness and hollow

`artifacts/make/r0001/product/cad/part_D.step.py --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-D.md`

part_D.step.py: 99.12 cm3 solid, grid 0.306 mm (211x212x234), 203338 surface samples, thickness resolved to 0.153 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.15) | PASS | 0.0% of surface below (0 of 203338 samples) |
| thickness distribution | PASS | median 27.50 mm, p95 66.01 mm, max 69.98 mm |
| hollowable at 1.20 mm wall | WARN | 75.89 of 99.12 cm3 (77%) in 1 pocket(s) |
| filament that would save | PASS | 11.38 cm3, 14.1 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.

## Proposal-format compatibility summary

The current source checker emitted the passing tables above and exited zero in the final verification pipeline. Its original bytes are preserved in the run evidence. The proposal parser requires this legacy result spelling; it summarizes source print checks only and does not establish a manufactured sample.

RESULT: printable at this wall
