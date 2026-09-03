# Moonchase Fox CAD project

One monolithic, support-free desk rocker. `moonchase_fox.step.py` is the printable entry; `moonchase_fox_lib.py` owns all parameters and feature builders.

- Printed parts: 1
- Purchased parts: 0
- Assembly: none
- Print stance: flat back at Z=0
- Bed: `--bed 220x220x220`
- Nozzle used for verification: 0.4 mm
- Material assumption: rigid PLA/PETG-like filament
- Supports: none required by the declared flat orientation

Build and final verification:

```text
python <cad-skill>/scripts/verify_project cad/moonchase_fox --fresh --exports --strict-fit
```

The digital center-of-mass/curvature check establishes restoring geometry only. Rocking duration, damping, surface friction, durability, and physical print quality remain unverified until tested on a real print.

