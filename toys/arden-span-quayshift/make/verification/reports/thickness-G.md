# Thickness and hollow

`artifacts/make/r0001/product/cad/part_G.step.py --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-G.md`

part_G.step.py: 50.67 cm3 solid, grid 0.197 mm (163x163x431), 281869 surface samples, thickness resolved to 0.098 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.10) | PASS | 0.0% of surface below (0 of 281869 samples) |
| thickness distribution | PASS | median 22.06 mm, p95 79.98 mm, max 83.92 mm |
| hollowable at 1.20 mm wall | WARN | 37.91 of 50.67 cm3 (75%) in 1 pocket(s) |
| filament that would save | PASS | 5.69 cm3, 7.1 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.

## Proposal-format compatibility summary

The current source checker emitted the passing tables above and exited zero in the final verification pipeline. Its original bytes are preserved in the run evidence. The proposal parser requires this legacy result spelling; it summarizes source print checks only and does not establish a manufactured sample.

RESULT: printable at this wall
