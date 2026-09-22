# Rainward Lowflow CAD

Source modification of the immutable Rainward Flow baseline. Units mm, XY bed, +Z up. All35 loose components retain separate `part_*.step.py` entries, with base at Z0. `rainward_lib.py` owns source parameters, unchanged counter/die/cup builders and corrected Sun relief. `rainward.step.py` is the single combined presentation entry and is not a print target.

The physical parts have no fixed joints, fasteners, connector insertion or retention assembly. They are loose game pieces placed and lifted by players. Aligned stacks have free separation. The legal capture illustration is a before/after board state, not a coupled mechanism or simulated handling motion.

Board outline190×190, deck16, lane top16.8, center17 with radius24.24 broad flat sectors, twenty0.8mm channels and four1.6mm channels, floor16. Four10×0.8 radial capsule markers centered radius65 have maximum top17 and are between lane6/7,12/13,18/19,24/1. Long lane edges have0.15 top rounding; original exterior scallop contour remains unchanged. All board faces share the same material color. No endpoints have dots.

Counters12×8×4,15 per side, original Bezier curves. Five preserved radial stations85,72,59,46,33; three aligned layers at16.8,20.8,24.8. The radius24 capture circle supports six original sites at x=-12,0,12 and y=-5,+5. Dice16, conical recessed pips radius1 depth1.1; cups42OD38ID28high2floor.

--bed 200x200x200

Generate explicit entries with the materialized CAD `gen ... --write` tool. Current exact STEP geometry and contact checks are in `measure/check_geometry.py` and `measure/check_fit.py`; the unchanged rules/state trace is in `measure/check_rules.py`. Final verification report is `measure/verification-pipeline.md`. Canonical rendering uses exact STEP solids, native triangle shading and dark actual pip-recess faces. No geometry is painted onto images.

This is digital evidence only. Partial tail overhang is measured, not hidden. Physical print quality, fit, real stack stability, handling and dice fairness have not been tested.

The split-tail builder normalizes only sub-picometer endpoint roundoff before extrusion and on the finished vertices. This prevents alternate equivalent STEP number formatting at the preserved0.1mm coordinate. The Bezier control points, component dimensions and features remain unchanged; the separate source/shape preservation audit records this implementation detail explicitly.
