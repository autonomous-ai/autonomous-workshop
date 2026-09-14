# Thickness and hollow

`artifacts/make/r0001/product/cad/part_tray.step.py --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-tray.md`

part_tray.step.py: 192.52 cm3 solid, grid 0.354 mm (525x525x39), 378714 surface samples, thickness resolved to 0.177 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.18) | PASS | 0.0% of surface below (0 of 378714 samples) |
| thickness distribution | PASS | median 3.89 mm, p95 12.03 mm, max 183.96 mm |
| hollowable at 1.20 mm wall | WARN | 107.65 of 192.52 cm3 (56%) in 1 pocket(s) |
| filament that would save | PASS | 16.15 cm3, 20.0 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.

## Proposal-format compatibility summary

The current source checker emitted the passing tables above and exited zero in the final verification pipeline. Its original bytes are preserved in the run evidence. The proposal parser requires this legacy result spelling; it summarizes source print checks only and does not establish a manufactured sample.

RESULT: printable at this wall
