# Thickness and hollow

`artifacts/make/r0001/product/cad/part_B.step.py --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-B.md`

part_B.step.py: 90.04 cm3 solid, grid 0.277 mm (348x293x117), 255753 surface samples, thickness resolved to 0.139 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.14) | PASS | 0.0% of surface below (0 of 255753 samples) |
| thickness distribution | PASS | median 21.90 mm, p95 75.81 mm, max 95.08 mm |
| hollowable at 1.20 mm wall | WARN | 67.91 of 90.04 cm3 (75%) in 1 pocket(s) |
| filament that would save | PASS | 10.19 cm3, 12.6 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.

## Proposal-format compatibility summary

The current source checker emitted the passing tables above and exited zero in the final verification pipeline. Its original bytes are preserved in the run evidence. The proposal parser requires this legacy result spelling; it summarizes source print checks only and does not establish a manufactured sample.

RESULT: printable at this wall
