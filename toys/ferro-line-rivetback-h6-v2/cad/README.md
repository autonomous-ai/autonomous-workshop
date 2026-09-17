# RIVETBACK H-6 CAD project

Original text-derived fixed-pose mecha hexapod kit. The combined entry is `rivetback.step.py`; each `part_<role>.step.py` is a separately printable unique component in its declared bed pose.

The assembly is approximately 210 × 190 × 96 mm. Individual components target a 180 × 180 × 180 mm bed and a 0.4 mm nozzle.

No motion, firing, illumination, physical print, insertion force, durability, or printer-specific fit is claimed. Pegs, slots, and keyed joints are nominal CAD geometry. The canonical static assembly uses keyed tenon-and-mortise alignment; the digital checks establish modeled clearance and non-interference, not real-world retention or assembly feel. The joint-lock-pin generator is an optional standalone spare and is not used in the canonical assembly.

Colors: industrial yellow armor, charcoal structure, and cyan passive conduit/sensor inserts.

Rebuild all entries with the materialized CAD `scripts/gen ... --write` tool. Run `scripts/check_layout cad`, then the per-component and combined Make rounds, and finally `scripts/verify_project cad --strict-fit --print-gates --nozzle 0.4 --bed 180x180x180 --report cad/measure/verification-pipeline.md` from the product workspace.
