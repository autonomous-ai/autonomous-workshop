# Thickness and hollow

`artifacts/make/r0001/product/cad-project/part_tender_truck_keeper_front.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad-project/measure/thickness-tender_truck_keeper_front.md`

artifacts/make/r0001/product/cad-project/part_tender_truck_keeper_front.stl: 0.73 cm3 solid, grid 0.133 mm (140x132x23), 41737 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 41737 samples) |
| thickness distribution | PASS | median 2.40 mm, p95 17.93 mm, max 18.00 mm |
| hollowable at 1.20 mm wall | PASS | 0.00 of 0.73 cm3 (0%) in 0 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
