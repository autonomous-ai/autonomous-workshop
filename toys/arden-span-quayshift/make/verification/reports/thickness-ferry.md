# Thickness and hollow

`artifacts/make/r0001/product/cad/part_ferry.step.py --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-ferry.md`

part_ferry.step.py: 5.73 cm3 solid, grid 0.133 mm (200x188x155), 123512 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 123512 samples) |
| thickness distribution | PASS | median 14.33 mm, p95 25.93 mm, max 28.07 mm |
| hollowable at 1.20 mm wall | WARN | 3.22 of 5.73 cm3 (56%) in 1 pocket(s) |
| filament that would save | PASS | 0.48 cm3, 0.6 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.

## Proposal-format compatibility summary

The current source checker emitted the passing tables above and exited zero in the final verification pipeline. Its original bytes are preserved in the run evidence. The proposal parser requires this legacy result spelling; it summarizes source print checks only and does not establish a manufactured sample.

RESULT: printable at this wall
