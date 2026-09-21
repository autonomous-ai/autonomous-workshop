# RIVETBACK H-6 V4 CAD project

Reference-guided, fixed-pose mecha hexapod display kit. The combined entry is
`rivetback.step.py`; every `part_<role>.step.py` entry is a separately printable
component in its declared bed orientation.

The canonical V4 assembly is approximately 242.0 x 147.6 x 77.7 mm and contains
61 labeled occurrences. It uses 15 unique roles: chassis, three base carapace
plates, three secondary dorsal armor plates, hip yoke, upper beam and armor,
lower beam and armor, energy conduit, foot, and joint lock pin. Four older
weapon/sensor generators remain as legacy standalone files but are not present
in the V4 assembly.

The visual scheme is industrial yellow armor over a charcoal mechanical frame,
with pale conduit loops and dark-steel Allen-style joint pins. There is no
weapon or forward sensor/cannon cluster in the canonical V4 assembly.

The joints are rigid keyed tenon-and-mortise interfaces reinforced by removable
3.2 mm through-pins with 8 mm round heads and hexagonal recesses. They are not
free-moving ball joints, and the model is not digitally articulated. Nominal
CAD clearances are 0.20-0.25 mm per side.

Individual parts target supportless FDM printing with a 0.4 mm nozzle on a
180 x 180 x 180 mm bed. Digital checks establish modeled clearance, thickness,
bed fit, and non-interference; they do not establish physical snap force,
durability, printer-specific compensation, or a successful real-world print.

Rebuild with the materialized `scripts/gen ... --write` workflow, then run the
integrated verifier with strict-fit and print gates before release.
