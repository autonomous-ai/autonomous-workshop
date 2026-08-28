# Thickness and hollow

`artifacts/make/r0002/product/cad/comet_heist/part_gate_bridge.stl --nozzle 0.4 --report artifacts/make/r0002/product/cad/comet_heist/measure/thickness-gate_bridge.md`

artifacts/make/r0002/product/cad/comet_heist/part_gate_bridge.stl: 34.40 cm3 solid, grid 0.239 mm (279x464x88), 210380 surface samples, thickness resolved to 0.120 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.12) | PASS | 0.0% of surface below (0 of 210380 samples) |
| thickness distribution | PASS | median 12.93 mm, p95 65.49 mm, max 109.91 mm |
| hollowable at 1.20 mm wall | WARN | 21.34 of 34.40 cm3 (62%) in 1 pocket(s) |
| filament that would save | PASS | 3.20 cm3, 4.0 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
