# Thickness and hollow

`artifacts/make/r0001/product/cad/part_H.step.py --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-H.md`

part_H.step.py: 38.76 cm3 solid, grid 0.179 mm (179x179x363), 277911 surface samples, thickness resolved to 0.089 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.09) | PASS | 0.0% of surface below (0 of 277911 samples) |
| thickness distribution | PASS | median 21.98 mm, p95 60.04 mm, max 63.97 mm |
| hollowable at 1.20 mm wall | WARN | 28.06 of 38.76 cm3 (72%) in 1 pocket(s) |
| filament that would save | PASS | 4.21 cm3, 5.2 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.

## Proposal-format compatibility summary

The current source checker emitted the passing tables above and exited zero in the final verification pipeline. Its original bytes are preserved in the run evidence. The proposal parser requires this legacy result spelling; it summarizes source print checks only and does not establish a manufactured sample.

RESULT: printable at this wall
