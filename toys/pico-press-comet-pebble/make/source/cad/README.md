# Comet Pebble CAD

Comet Pebble is one support-free skew-keel rattleback. The twisted lower
curvature and upper mass axes are part of the solid itself; there is no
separate mechanism. `comet_pebble.step.py` is the parametric source and its
sibling STEP/STL files are generated outputs.

- Print stance: the broad elliptical landing foot is on the XY bed at Z=0.
- Declared bed: `--bed 220x220x220`.
- Nominal envelope: about 68 x 45 x 34 mm.
- No assembly, supports, electronics, glue, hardware, or purchased parts.
- Suggested material/process: PLA or PETG, 0.4 mm nozzle, 0.20 mm layers,
  three perimeters, 100% infill for closest correspondence to the uniform-
  density balance model, and a brim only if bed adhesion requires it.
- The digitally checked center of mass projects inside the 34.4 x 20.4 mm landing
  ellipse. The lower section axes rotate +10 degrees while the upper sections
  turn to -17 degrees; the exact uniform-density inertia axis is 10.26 degrees
  from the lower-rail axis.
  Motion character and repeatable real-world settling remain physically
  unverified until the exact print is tested on the intended desk surface.

Rebuild from the product workspace with the materialized CAD skill:

```text
python .agents/skills/cad/scripts/gen artifacts/make/r0001/product/cad/comet_pebble.step.py --write
python .agents/skills/cad/scripts/verify_project artifacts/make/r0001/product/cad --fresh --exports --strict-fit
```
