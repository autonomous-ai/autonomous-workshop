# Thickness and hollow

`artifacts/make/r0001/product/cad/veinwake/part_tooth_4.step.py --nozzle 0.4 --report artifacts/make/r0001/product/cad/veinwake/measure/thickness-tooth_4.md`

part_tooth_4.step.py: 7.61 cm3 solid, grid 0.133 mm (215x215x200), 141156 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 141156 samples) |
| thickness distribution | PASS | median 19.00 mm, p95 27.93 mm, max 28.53 mm |
| hollowable at 1.20 mm wall | WARN | 4.75 of 7.61 cm3 (62%) in 1 pocket(s) |
| filament that would save | PASS | 0.71 cm3, 0.9 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.

## Proposal-format compatibility summary

Manager-authored format bridge from the unchanged passing table above and final verifier exit 0; not an additional measurement. Raw reporter bytes: `raw-verifier-reports/thickness-tooth_4.md`, SHA-256 `401045c500c2d2ddaf13a7532c4ff96cc4491937d095d69d49458634cc7a0021`.

RESULT: printable at this wall
