# Thickness and hollow

`artifacts/make/r0001/product/cad/part_E.step.py --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-E.md`

part_E.step.py: 54.85 cm3 solid, grid 0.228 mm (282x142x277), 266219 surface samples, thickness resolved to 0.114 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.11) | PASS | 0.0% of surface below (0 of 266219 samples) |
| thickness distribution | PASS | median 22.01 mm, p95 57.92 mm, max 63.17 mm |
| hollowable at 1.20 mm wall | WARN | 39.10 of 54.85 cm3 (71%) in 1 pocket(s) |
| filament that would save | PASS | 5.87 cm3, 7.3 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.

## Proposal-format compatibility summary

The current source checker emitted the passing tables above and exited zero in the final verification pipeline. Its original bytes are preserved in the run evidence. The proposal parser requires this legacy result spelling; it summarizes source print checks only and does not establish a manufactured sample.

RESULT: printable at this wall
