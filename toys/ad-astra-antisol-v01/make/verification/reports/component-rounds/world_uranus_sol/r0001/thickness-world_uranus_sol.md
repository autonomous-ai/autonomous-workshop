# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_world_uranus_sol.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/world_uranus_sol/r0001/thickness-world_uranus_sol.md`

part_world_uranus_sol.step.py: 9.91 cm3 solid, grid 0.140 mm (246x247x184), 171891 surface samples, thickness resolved to 0.070 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 171891 samples) |
| thickness distribution | PASS | median 21.91 mm, p95 33.39 mm, max 33.74 mm |
| hollowable at 1.20 mm wall | WARN | 6.08 of 9.91 cm3 (61%) in 1 pocket(s) |
| filament that would save | PASS | 0.91 cm3, 1.1 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
