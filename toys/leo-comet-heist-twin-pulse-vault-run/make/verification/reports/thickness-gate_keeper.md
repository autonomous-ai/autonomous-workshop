# Thickness and hollow

`artifacts/make/r0002/product/cad/comet_heist/part_gate_keeper.stl --nozzle 0.4 --report artifacts/make/r0002/product/cad/comet_heist/measure/thickness-gate_keeper.md`

artifacts/make/r0002/product/cad/comet_heist/part_gate_keeper.stl: 1.27 cm3 solid, grid 0.133 mm (215x80x69), 54981 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 54981 samples) |
| thickness distribution | PASS | median 8.00 mm, p95 27.93 mm, max 28.00 mm |
| hollowable at 1.20 mm wall | WARN | 0.34 of 1.27 cm3 (27%) in 1 pocket(s) |
| filament that would save | PASS | 0.05 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
