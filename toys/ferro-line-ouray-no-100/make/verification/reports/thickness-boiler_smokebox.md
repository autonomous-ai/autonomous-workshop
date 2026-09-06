# Thickness and hollow

`artifacts/make/r0001/product/cad-project/part_boiler_smokebox.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad-project/measure/thickness-boiler_smokebox.md`

artifacts/make/r0001/product/cad-project/part_boiler_smokebox.stl: 36.15 cm3 solid, grid 0.170 mm (157x175x381), 296026 surface samples, thickness resolved to 0.085 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.09) | PASS | 0.0% of surface below (0 of 296026 samples) |
| thickness distribution | PASS | median 24.93 mm, p95 63.98 mm, max 63.98 mm |
| hollowable at 1.20 mm wall | WARN | 26.70 of 36.15 cm3 (74%) in 1 pocket(s) |
| filament that would save | PASS | 4.01 cm3, 5.0 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
