# Thickness and hollow

`artifacts/make/r0001/product/cad/part_F.step.py --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-F.md`

part_F.step.py: 51.54 cm3 solid, grid 0.217 mm (296x148x272), 291406 surface samples, thickness resolved to 0.109 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.11) | PASS | 0.0% of surface below (0 of 291406 samples) |
| thickness distribution | PASS | median 21.83 mm, p95 53.86 mm, max 63.20 mm |
| hollowable at 1.20 mm wall | WARN | 34.25 of 51.54 cm3 (66%) in 1 pocket(s) |
| filament that would save | PASS | 5.14 cm3, 6.4 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.

## Proposal-format compatibility summary

The current source checker emitted the passing tables above and exited zero in the final verification pipeline. Its original bytes are preserved in the run evidence. The proposal parser requires this legacy result spelling; it summarizes source print checks only and does not establish a manufactured sample.

RESULT: printable at this wall
