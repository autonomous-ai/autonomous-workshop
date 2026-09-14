# Thickness and hollow

`artifacts/make/r0001/product/cad/veinwake/part_bubble_3.step.py --nozzle 0.4 --report artifacts/make/r0001/product/cad/veinwake/measure/thickness-bubble_3.md`

part_bubble_3.step.py: 10.12 cm3 solid, grid 0.133 mm (215x215x200), 169822 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 169822 samples) |
| thickness distribution | PASS | median 22.13 mm, p95 27.93 mm, max 32.87 mm |
| hollowable at 1.20 mm wall | WARN | 6.70 of 10.12 cm3 (66%) in 1 pocket(s) |
| filament that would save | PASS | 1.01 cm3, 1.2 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.

## Proposal-format compatibility summary

Manager-authored format bridge from the unchanged passing table above and final verifier exit 0; not an additional measurement. Raw reporter bytes: `raw-verifier-reports/thickness-bubble_3.md`, SHA-256 `9b1fa9dbb1c0d1c388bbdeea8ca57a86aec30713423cb16e8ffe501146ac0e3b`.

RESULT: printable at this wall
