# Thickness and hollow

`artifacts/make/r0001/product/cad-project/part_tender_truck_front.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad-project/measure/thickness-tender_truck_front.md`

artifacts/make/r0001/product/cad-project/part_tender_truck_front.stl: 1.75 cm3 solid, grid 0.133 mm (170x50x162), 98295 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 98295 samples) |
| thickness distribution | PASS | median 3.93 mm, p95 20.93 mm, max 22.00 mm |
| hollowable at 1.20 mm wall | WARN | 0.21 of 1.75 cm3 (12%) in 4 pocket(s) |
| filament that would save | PASS | 0.03 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
