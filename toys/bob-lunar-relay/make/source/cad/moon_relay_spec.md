# Lunar Relay CAD brief

- Model: three-part palm-sized kinetic desk-toy assembly.
- Task type: new parametric assembly; STEP is primary, STL exports are secondary.
- Units: millimetres.
- Coordinate convention: assembly origin at the base footprint centre; XY is the desk plane; +Z is up; the rocker/axle axis is +Y.
- Overall envelope: 92 × 54 × 25 mm in the neutral pose.
- Functional idea: a rigid beam pivots on a printed axle. Its two cratered 22 mm moons sit 60 mm centre-to-centre, so pressing one produces an equal opposite rise.
- Printed parts: `lunar_base`, `moon_rocker`, and `quarter_turn_axle`; no bought parts.
- Base: 4 mm plate, two 5 mm pivot cheeks, and 2 mm radial walls around the two moon wells.
- Rocker: 14 mm thick monolithic beam/moon body; neutral pivot height 17.5 mm; declared travel ±8°; rise difference about 8.35 mm.
- Axle: 6 mm round shaft, broad head, and self-supporting tapered locking tab. The axle inserts with the tab horizontal and locks after a 90° turn.
- Fits: all female dimensions derive from the male using `cadfits.slot_for`; moving bores use the `free` class (0.40 mm per side).
- Print stances: base flat as assembled; rocker flat on its broad underside; axle upright on its broad head with a 41° or steeper self-supporting tab transition.
- Safety intent: crater rims visually and physically guard the descending moon edge; the base floor is the hard end stop beyond the declared sweep. Use is limited to pressing moon tops.
- Paths: `moon_relay.step.py` is the combined review entry; `part_*.step.py` are the three printable entries.
- Validation: layout, per-part bed/volume checks, local fit/spec audit, rigid-body motion/capture checks, refs/positioning, per-solid topology, assembly interference, per-part STL mesh and wall-thickness gates, and direct rendered mesh review.
- Evidence boundary: no successful print, physical fit, durability, force, or human response is claimed.

Dimension provenance: the Wish fixes palm scale, interaction, support-free printing, and no hardware. All numeric dimensions are design assumptions selected for a compact 0.4 mm-nozzle FDM candidate and are identified in `moon_relay_lib.py`.
